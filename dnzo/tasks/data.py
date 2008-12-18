#
#  If we've got a "model" layer in the MVC pattern, this is it.
#  This collection of methods retrieves things from the database
#  and also performs (or will perform) caching when necessary.
#

from google.appengine.api.users import get_current_user
from google.appengine.api import memcache

from tasks.errors import *
from tasks.models import *
from util.misc import urlize, indexize, zpad, param
from util.parsing import parse_date

from datetime import datetime

import re

#
#  This specifies how long the maximum indexized value can be.
#  This essentially limits the maximum number of records to 
#  MAX_INDEX_LENGTH index records per unique indexed value,
#  but also restricts the resultset from index queries to results
#  appearing in the first MAX_INDEX_LENGTH characters of the value.
#
MAX_INDEX_LENGTH = 50

### USERS ###

def users_equal(a,b):
  if a is None and b is None:
    return True
  if a is None or b is None:
    return False
  if a.is_saved() and b.is_saved():
    return a.key().id_or_name() == b.key().id_or_name()
  return False
  
def get_dnzo_user():
  google_user = get_current_user()
  if not google_user:
    return None
    
  dnzo_user = memcache.get(key=google_user.email())
  if not dnzo_user:
    dnzo_user = TasksUser.gql('WHERE user=:user', user=google_user).get()
    memcache.set(key=google_user.email(), value=dnzo_user)

  return dnzo_user
  
### TASK LISTS ###

def get_task_list(user, name):
  return TaskList.get_by_key_name(TaskList.name_to_key_name(name), parent=user)

def user_lists_key(user):
  return "%s-lists" % str(user.key())
def clear_lists_memcache(user):
  memcache.delete(key=user_lists_key(user))
def clear_user_memcache(user):
  memcache.delete(key=user.user.email())
def set_user_memcache(user):
  memcache.set(key=user.user.email(), value=user)

def add_task_list(user, list_name):
  def txn(user, list_name):
    short_name = get_new_list_name(user, list_name)
    new_list = TaskList(parent=user, 
      key_name=TaskList.name_to_key_name(short_name),
      short_name=short_name,
      name=list_name)
    new_list.put()
    
    user = db.get(user.key())
    user.lists_count += 1
    user.put()
    
    set_user_memcache(user)
    
    return short_name
    
  short_name = db.run_in_transaction(txn, user, list_name)
  
  clear_lists_memcache(user)
  
  return get_task_list(user, short_name)

def delete_task_list(user, task_list):
  def txn(task_list, deleted_tasks):
    # Make sure we do not double count
    task_list = db.get(task_list.key())
    if task_list.deleted:
      return 
      
    task_list.deleted = True
    task_list.put()
    
    user = task_list.parent()
    undo = Undo(task_list=task_list, parent=user)
    undo.list_deleted = True
    
    for task in deleted_tasks:
      undo.deleted_tasks.append(task.key())
    undo.put()
    
    user.tasks_count -= len(deleted_tasks)
    user.lists_count -= 1
    user.put()
    
    set_user_memcache(user)
    
    return undo
    
  # TODO: Remove possible data inconsistency if the count between 
  # when we execute this query and when the count is changed changes.
  deleted_tasks = Task.gql("WHERE task_list=:list AND archived=:archived AND deleted=:deleted",
                           list=task_list, archived=False, deleted=False).fetch(100)
  undo = db.run_in_transaction(txn, task_list, deleted_tasks)

  clear_lists_memcache(user)

  return undo
  
def undelete_task_list(user, task_list):
  def txn(task_list, deleted_tasks):
    task_list = db.get(task_list.key())
    if not task_list.deleted:
      return
      
    task_list.deleted = False
    task_list.put()
    
    user = task_list.parent()
    user.lists_count += 1
    user.tasks_count += len(deleted_tasks)
    user.put()
    
    set_user_memcache(user)

  # TODO: Remove possible data inconsistency if the count between 
  # when we execute this query and when the count is changed changes.
  deleted_tasks = Task.gql("WHERE task_list=:list AND archived=:archived AND deleted=:deleted",
                           list=task_list, archived=False, deleted=False).fetch(100)

  db.run_in_transaction(txn, task_list, deleted_tasks)
  
  clear_lists_memcache(user)
  
def get_task_lists(user, limit=10):
  lists_key = user_lists_key(user)
  task_lists = memcache.get(key=lists_key)
  if not task_lists:
    query = TaskList.gql(
      'WHERE ANCESTOR IS :user AND deleted=:deleted ORDER BY name ASC', 
      user=user, deleted=False
    )
    task_lists = query.fetch(limit)
    memcache.set(key=lists_key, value=task_lists)
    
  return task_lists
  
def get_new_list_name(user, new_name):
  new_name = urlize(new_name)
  appendage = ''
  i = 1
  while get_task_list(user, new_name + appendage) is not None:
    appendage = "_%s" % i
    i += 1
    
  return new_name + appendage
  
def get_completed_tasks(task_list, limit=100):
  tasks = Task.gql('WHERE task_list=:list AND archived=:archived AND complete=:complete', 
                   list=task_list, archived=False, complete=True)
  return tasks.fetch(limit)
    
  
### TASKS ###

def save_task(user,task):
  if not task.is_saved():
    add_task(task)
  else:
    task.put()
  
  if task.project_index:
    save_project(user, task.project)
  if len(task.contexts) > 0:
    save_contexts(user, task.contexts)
  
def add_task(task):
  def txn(task):
    if task.is_saved():
      return
    
    task.put()
    
    user = task.parent()
    user.tasks_count += 1
    user.put()
    
    set_user_memcache(user)
    
  db.run_in_transaction(txn, task)

def delete_task(user, task):
  def txn(task, undo):
    task = db.get(task.key())
    if task.deleted:
      return
      
    task.deleted = True
    task.task_list = None
    task.put()
    
    user = task.parent()
    user.tasks_count -= 1
    user.put()

    undo.put()
    
    set_user_memcache(user)

  undo = Undo(task_list=task.task_list, parent=user)
  undo.deleted_tasks.append(task.key())
      
  db.run_in_transaction(txn, task, undo)

  return undo

def undelete_task(task, task_list):
  def txn(task, task_list):
    task = db.get(task.key())
    was_deleted = task.deleted
    task.deleted = False
    task.task_list = task_list
    task.put()
    
    if not was_deleted:
      return
    
    user = task.parent()
    user.tasks_count += 1
    user.put()
    
    set_user_memcache(user)
    
  db.run_in_transaction(txn, task, task_list)

def update_task_with_params(user, task, params):
  if param('complete', params) == "true":
    task.complete = True
    task.completed_at = datetime.utcnow()
  else:
    task.complete = False
    task.completed_at = None
  
  task.body = param('body', params)
  
  raw_project = param('project',params,None)
  if raw_project:
    raw_project = raw_project.strip()
    if len(raw_project) > 0:
      task.project       = raw_project
      task.project_index = urlize(raw_project)
    else:
      task.project = None
      task.project_index = None
  
  raw_contexts = param('contexts', params,None)
  if raw_contexts:
    task.contexts = []
    raw_contexts = re.findall(r'[A-Za-z_-]+', raw_contexts)
    for raw_context in raw_contexts:
      task.contexts.append(urlize(raw_context))
  
  raw_due_date = param('due_date', params, None)
  if raw_due_date:
    task.due_date = parse_date(raw_due_date, user.timezone_offset_mins)
    
  

### PROJECTS ###

def get_project(user, project_name):
  return Project.get_by_key_name(
             Project.name_to_key_name(project_name),
             parent=user
         )

def save_project(user, project_name):
  project = get_project(user, project_name)
  
  if not project:
    project = create_project(user, project_name)
    
  else:
    for index in project.indexes:
      # TODO: update in a transaction?
      index.last_used_at = datetime.utcnow()
      index.put()
    
  return project
  
def create_project(user, project_name):
  def txn(user, project):
    project.put()
    name = indexize(project.name)[0:MAX_INDEX_LENGTH]
    tokens = re.split(r'\s+', name)
    for i in range(0,len(tokens)):
      token = ' '.join(tokens[i:])
      index = ProjectIndex(parent=user, index=token, name=project.name, project=project)
      index.put()
    
  short_name = urlize(project_name)
  key_name = Project.name_to_key_name(project_name)
  project = Project(
    parent=user, 
    key_name=key_name,
    name=project_name, 
    short_name=short_name
  )
    
  db.run_in_transaction(txn, user, project)

  return project
  
def find_projects_by_name(user, project_name, limit=5):
  indexed_name = indexize(project_name)
  
  indexes = ProjectIndex.gql(
    "WHERE index >= :start AND index < :end AND ANCESTOR IS :user",
    start=indexed_name, end=zpad(indexed_name), user=user
  )
  
  return sorted_by_last_used(indexes, limit)
  
def get_project_by_short_name(user, short_name):
  project = Project.gql(
    'WHERE ANCESTOR IS :user AND short_name=:short_name ' + 
    'ORDER BY created_at DESC',
    user=user, short_name=short_name
  ).get()
  
  if project:
    return project.name
  return None
  
  
### CONTEXTS ###

def get_context(user, context_name):
  return Context.get_by_key_name(
    Context.name_to_key_name(context_name),
    parent=user
  )

def save_contexts(user, contexts):
  for context in contexts:
    save_context(user, context)
  
def save_context(user, context_name):
  context = get_context(user,context_name)
  if not context:
    context = Context(
      parent=user,
      name=context_name,
      key_name=Context.name_to_key_name(context_name)
    )
  context.last_used_at = datetime.utcnow()
  context.put()
  
def find_contexts_by_name(user, context_name, limit=5):
  indexed_name = urlize(context_name)
  
  contexts = Context.gql(
    "WHERE name >= :start AND name < :end AND ANCESTOR IS :user",
    start=indexed_name, end=zpad(indexed_name), user=user
  )
  
  return sorted_by_last_used(contexts, limit)

  
### UNDOS ###

def do_undo(user, undo):
  for task in undo.find_deleted():
    undelete_task(task, undo.task_list)
    
  for task in undo.find_archived():
    task.archived = False
    task.put()
    
  if undo.list_deleted:
    undelete_task_list(user, undo.task_list)
    
  undo.delete()

  
### MISC ###

def sorted_by_last_used(collection, limit):
  names_last_used = {}
  for index in collection:
    name, last_used_at = index.name, index.last_used_at
    if name not in names_last_used or last_used_at > names_last_used[name]:
      names_last_used[name] = last_used_at

  names = names_last_used.items()
  names.sort(key=lambda item: item[1])
  names.reverse()
  names = map(lambda item: item[0], names)

  return names[0:limit]
