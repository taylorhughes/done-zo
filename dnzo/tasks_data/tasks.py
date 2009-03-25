from google.appengine.api import memcache
from google.appengine.ext import db

from tasks_data.models import Task

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
  
### TASKS ###

def get_tasks_from_datastore(task_list):
  wheres = ['task_list=:task_list AND archived=:archived'] 
  params = { 'task_list': task_list, 'archived': False }

  gql = 'WHERE %s ORDER BY created_at ASC' % ' AND '.join(wheres)

  return Task.gql(gql, **params).fetch(RESULT_LIMIT)
    
def tasks_memcache_key(task_list):
  return '%s-tasks' % str(task_list.key())
  
def get_tasks_from_memcache(task_list):
  return memcache.get(tasks_memcache_key(task_list))
  
def set_tasks_memcache(task_list,tasks):
  if not task_list:
    return
  return memcache.set(tasks_memcache_key(task_list), tasks)

def get_tasks(task_list, project_index=None, context=None, due_date=None):
  tasks = get_tasks_from_memcache(task_list)
  if not tasks:
    tasks = get_tasks_from_datastore(task_list)
    set_tasks_memcache(task_list, tasks)

  if context:
    tasks = filter(lambda t: context in t.contexts, tasks)
  if project_index:
    tasks = filter(lambda t: project_index == t.project_index, tasks)
  if due_date:
    tasks = filter(lambda t: due_date == t.due_date, tasks)
    
  return tasks
  
def save_task(user,task):
  if not task.is_saved():
    add_task(task)
  else:
    task.put()
  
  if task.project_index:
    save_project(user, task.project)
  if len(task.contexts) > 0:
    save_contexts(user, task.contexts)
  
  set_tasks_memcache(task.task_list, None)
  save_user(user)
  
def add_task(task):
  task_list = task.task_list
  if task_list.active_tasks_count >= MAX_ACTIVE_TASKS:
    return
    
  def txn():
    if task.is_saved():
      return
    
    task.put()
    
    task_list.active_tasks_count += 1
    task_list.put()
    
  db.run_in_transaction(txn)
  counting.task_added()

def delete_task(user, orig_task):
  def txn():
    task = db.get(orig_task.key())
    if task.deleted:
      return

    task_list = task.task_list
    task_list.active_tasks_count -= 1
    task_list.put()
    
    task.deleted = True
    task.task_list = None
    task.put()
  
  set_tasks_memcache(orig_task.task_list, None)
  db.run_in_transaction(txn)
  counting.task_deleted()

def undelete_task(orig_task, task_list):
  def txn():
    task = db.get(orig_task.key())
    was_deleted = task.deleted
    task.deleted = False
    task.task_list = task_list
    task.put()
    
    if not was_deleted:
      return
    
    task_list.active_tasks_count += 1
    task_list.put()
  
  set_tasks_memcache(task_list, None)
  db.run_in_transaction(txn)
  counting.task_undeleted()

def update_task_with_params(user, task, params):
  from util.misc import param, slugify
  
  if param('complete', params) == "true":
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
    
  
