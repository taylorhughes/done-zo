from google.appengine.api import memcache
from google.appengine.ext import db

from tasks_data.models import TaskList, Undo, Task
from tasks_data.users import save_user

### MEMCACHING ###

def user_lists_key(user):
  return "%s-lists" % str(user.key())
def clear_lists_memcache(user):
  memcache.delete(key=user_lists_key(user))
  
  
### TASK LISTS ###

def get_task_list(user, name):
  return TaskList.get_by_key_name(TaskList.name_to_key_name(name), parent=user)

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

    save_user(user)
    
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

    save_user(user)
    
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

    save_user(user)

  # TODO: Remove possible data inconsistency if the count between 
  # when we execute this query and when the count is changed changes.
  deleted_tasks = Task.gql("WHERE task_list=:list AND archived=:archived AND deleted=:deleted",
                           list=task_list, archived=False, deleted=False).fetch(100)

  db.run_in_transaction(txn, task_list, deleted_tasks)
  
  clear_lists_memcache(user)
  
def get_task_lists(user):
  lists_key = user_lists_key(user)
  try:
    task_lists = memcache.get(key=lists_key)
  except:
    import logging
    logging.exception("Could not retrieve memcached task_lists.")
    task_lists = None
    
  if not task_lists:
    query = TaskList.gql(
      'WHERE ANCESTOR IS :user AND deleted=:deleted ORDER BY name ASC', 
      user=user, deleted=False
    )
    task_lists = map(lambda row: row, query)
    memcache.set(key=lists_key, value=task_lists)
    
  return task_lists
  
def get_new_list_name(user, new_name):
  from util.misc import urlize
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
  
def archive_tasks(task_list, user):
  undo = Undo(task_list=task_list, parent=user)
  for task in get_completed_tasks(task_list):
    task.archived = True
    task.put()
    undo.archived_tasks.append(task.key())
  undo.put()
  return undo