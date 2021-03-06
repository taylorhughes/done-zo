# coding=utf-8

from google.appengine.api import memcache
from google.appengine.ext import db

from tasks_data.models import Task, TaskList

from tasks_data.users import save_user
from tasks_data.misc import save_project, save_contexts

import tasks_data.counting as counting

# This is actually a limitation of the datastore:
#   string types can only be 500 characters.
MAX_BODY_LENGTH    = 500

# This is mostly a factor of what it will make the UI 
# look like and how long and unwieldy URLs will get
MAX_PROJECT_LENGTH = 30
MAX_CONTEXT_LENGTH = 30

# Maximum number of undeleted, unarchived tasks for a list.
MAX_ACTIVE_TASKS   = 100

# Number of tasks to limit in queries
RESULT_LIMIT = 100

# This is the default set of tasks added for new users
# This collection is parsed the same way user input is parsed
DEFAULT_TASKS = (
  {
    'body':     u'Welcome to Done-zo!'
  },{
    'project':  u'Done-zo',
    'body':     u'You can organize your tasks by project →',
  },{
    'body':     u'... or by "context", which could mean where you need to be to complete the task. →',
    'contexts': u'home',
  },{
    'body':     u'You can also add due dates! →',
    'due_date': u'today',
  },
)

### TASKS ###

def get_tasks_from_datastore(dnzo_user, task_list=None, updated_since=None):
  wheres = [] 
  params = {}
  
  order = 'created_at ASC'
  
  if task_list:
    wheres.append("task_list=:task_list AND archived=:archived AND deleted=:deleted")
    params.update(task_list=task_list, archived=False, deleted=False)
    
  if updated_since:
    order = 'updated_at ASC'
    wheres.append("updated_at > :updated_since AND ANCESTOR IS :user")
    params.update(updated_since=updated_since, user=dnzo_user)

  gql = 'WHERE %s ORDER BY %s' % (' AND '.join(wheres), order)
  return Task.gql(gql, **params).fetch(RESULT_LIMIT)
  
def tasks_memcache_key(task_list):
  return '%s-tasks' % str(task_list.key())
  
def get_tasks_from_memcache(task_list):
  return memcache.get(tasks_memcache_key(task_list))
  
def set_tasks_memcache(task_list,tasks):
  if not task_list:
    return
  return memcache.set(tasks_memcache_key(task_list), tasks)

def get_tasks(dnzo_user, task_list=None, updated_since=None, project_index=None, context=None, due_date=None):
  assert task_list or updated_since, "Must provide a task_list -or- updated_since"
  if task_list:
    assert isinstance(task_list, TaskList)
  if updated_since:
    from datetime import datetime
    assert(isinstance(updated_since, datetime))
  
  tasks = None
  if updated_since:
    tasks = get_tasks_from_datastore(dnzo_user, task_list=task_list, updated_since=updated_since)
    
  elif task_list:
    tasks = get_tasks_from_memcache(task_list)
    if not tasks:
      tasks = get_tasks_from_datastore(dnzo_user, task_list=task_list)
      set_tasks_memcache(task_list, tasks)
  
        
  if context:
    tasks = filter(lambda t: context in t.contexts, tasks)
  if project_index:
    tasks = filter(lambda t: project_index == t.project_index, tasks)
  if due_date:
    tasks = filter(lambda t: due_date == t.due_date, tasks)
    
  return tasks
  
def get_archived_tasks(dnzo_user, start, stop):
  gql = 'WHERE ANCESTOR IS :user AND archived=:archived AND deleted=:deleted ' + \
        'AND completed_at >= :start AND completed_at < :stop ORDER BY completed_at DESC'

  tasks = Task.gql(gql, 
    user=dnzo_user,
    archived=True,
    deleted=False,
    start=start,
    stop=stop
  ).fetch(RESULT_LIMIT)
  
  return tasks
    
def save_task(user, task, task_archived_status_changed=False):
  if not task.is_saved():
    add_task(task)
    
  else:
    if task_archived_status_changed:
      def txn():
        increment = task.archived and 1 or -1
        task_list = task.task_list
        
        task_list.active_tasks_count -= increment
        task_list.archived_tasks_count += increment
              
        db.put([task, task_list])
        
      db.run_in_transaction(txn)
      
      if task.archived:
        counting.list_archived(task.task_list, [task])
      else:
        counting.list_unarchived(task.task_list, [task])
      
    else:
      task.put()

  
  if task.project_index:
    save_project(user, task.project)
  if len(task.contexts) > 0:
    save_contexts(user, task.contexts)
  
  set_tasks_memcache(task.task_list, None)
  save_user(user)
  
def task_list_can_add_task(task_list, task):
  return task.archived or task_list.active_tasks_count < MAX_ACTIVE_TASKS
  
def add_task(task):
  task_list = task.task_list
  if not task_list_can_add_task(task_list, task):
    return
    
  def txn():
    if task.is_saved():
      return
    
    task.put()
    
    # You can create new already-archived tasks
    if task.archived:
      task_list.archived_tasks_count += 1
    else:
      task_list.active_tasks_count += 1
      
    task_list.put()
    
  db.run_in_transaction(txn)
  counting.task_added(task.archived)

def delete_task(user, orig_task):
  def txn():
    task = db.get(orig_task.key())
    if task.deleted:
      return

    task_list = task.task_list
    if task.archived:
      task_list.archived_tasks_count -= 1
    else:
      task_list.active_tasks_count -= 1
        
    orig_task.deleted = True
    task.deleted = True
    
    db.put([task, task_list])
  
  set_tasks_memcache(orig_task.task_list, None)
  db.run_in_transaction(txn)
  counting.task_deleted(orig_task.archived)

def undelete_task(orig_task, task_list):
  def txn():
    task = db.get(orig_task.key())
    
    if not task.deleted:
      return
      
    task.deleted = False
    task.put()
    
    task_list.active_tasks_count += 1
    task_list.put()
  
  set_tasks_memcache(task_list, None)
  db.run_in_transaction(txn)
  counting.task_undeleted()

def update_task_with_params(user, task, params):
  from util.misc import param, slugify
  
  complete = param('complete', params, None)
  if complete is not None:
    if complete == "true":
      task.complete = True
      from datetime import datetime
      task.completed_at = datetime.utcnow()
    else:
      task.complete = False
      task.completed_at = None
  
  raw_body = param('body', params, None)
  if raw_body is not None:
    task.body = raw_body[:MAX_BODY_LENGTH]
  
  raw_project = param('project', params, None)
  if raw_project is not None:
    raw_project = raw_project.strip()[:MAX_PROJECT_LENGTH]
    if len(raw_project) > 0:
      task.project       = raw_project
      task.project_index = slugify(raw_project)
    else:
      task.project = None
      task.project_index = None
  
  raw_contexts = param('contexts', params, None)
  if raw_contexts is not None:
    import re
    task.contexts = []
    # if you update this, remember to change the logic
    # for updating the MRU contexts list in JavaScript.
    raw_contexts = re.split(r'[,;\s]+', raw_contexts)
    for raw_context in raw_contexts:
      slug = slugify(raw_context)[:MAX_CONTEXT_LENGTH]
      if len(slug) > 0:
        task.contexts.append(slug)
    task.contexts_index = " ".join(task.contexts)
  
  raw_due_date = param('due_date', params, None)
  if raw_due_date is not None:
    from util.human_time import parse_date
    task.due_date = None
    task.due_date = parse_date(raw_due_date, user.timezone_offset_mins)
    
  raw_sort_date = param('sort_date', params, None)
  if raw_sort_date is not None:
    import re
    import datetime
    try:
      date_pieces = [int(i) for i in re.split(r'\D+', raw_sort_date)]
      task.created_at = datetime.datetime(*date_pieces)
    except:
      import logging
      logging.exception("Invalid date string given as sort_date: %s", repr(raw_sort_date))
  
  archived = param('archived', params, None)
  if archived is not None:
    if archived == "true":
      if not task.complete:
        raise AssertionError, "Cannot archive uncompleted task."
      task.archived = True
    else:
      task.archived = False
    
  
