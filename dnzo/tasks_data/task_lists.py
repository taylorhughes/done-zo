from google.appengine.api import memcache
from google.appengine.ext import db

from tasks_data.models import TaskList, Undo, Task
from tasks_data.users import save_user

import tasks_data.counting as counting

MAX_LIST_NAME_LENGTH = 30
MAX_TASK_LISTS       = 10

# This is the default list name
DEFAULT_LIST_NAME = 'Tasks'


### MEMCACHING ###

def user_lists_key(user):
  return "%s-lists" % str(user.key())
def clear_lists_memcache(user):
  memcache.delete(key=user_lists_key(user))
  
  
### TASK LISTS ###

def can_add_list(user):
  return user.lists_count < MAX_TASK_LISTS

def get_task_list(user, name):
  return TaskList.get_by_key_name(TaskList.name_to_key_name(name), parent=user)

def add_task_list(user, list_name):
  def txn(old_user, list_name):
    user = db.get(old_user.key())
    if not can_add_list(user):
      return None
    
    user.lists_count += 1
    save_user(user)
    # the passed-in object should be consistent
    old_user.lists_count = user.lists_count
    
    short_name = get_new_list_name(user, list_name)
    new_list = TaskList(parent=user, 
      key_name=TaskList.name_to_key_name(short_name),
      short_name=short_name,
      name=list_name)
      
    new_list.put()
    
    return short_name
  
  short_name = db.run_in_transaction(txn, user, list_name[:MAX_LIST_NAME_LENGTH])
  
  if short_name:
    clear_lists_memcache(user)
    counting.list_added()
    return get_task_list(user, short_name)
  else:
    return None

def delete_task_list(user, orig_task_list):
  def txn():
    # Make sure we do not double count
    task_list = db.get(orig_task_list.key())
    if task_list.deleted:
      return 
      
    task_list.deleted = True
    task_list.put()
    
    user = task_list.parent()
    
    user.lists_count -= 1

    save_user(user)
    
  db.run_in_transaction(txn)
  deleted_tasks = Task.gql("WHERE task_list=:list AND archived=:archived AND deleted=:deleted",
                           list=orig_task_list, archived=False, deleted=False).fetch(100)
  counting.list_deleted(orig_task_list, deleted_tasks)
  
  clear_lists_memcache(user)

  return deleted_tasks
  
def undelete_task_list(user, orig_task_list):
  def txn():
    task_list = db.get(orig_task_list.key())
    if not task_list.deleted:
      return
      
    task_list.deleted = False
    task_list.put()
    
    user = task_list.parent()
    user.lists_count += 1

    save_user(user)
  
  db.run_in_transaction(txn)
  
  # TODO: Remove possible data inconsistency if the count between 
  # when we execute this query and when the count is changed changes.
  deleted_tasks = Task.gql("WHERE task_list=:list AND archived=:archived AND deleted=:deleted",
                           list=orig_task_list, archived=False, deleted=False).fetch(100)
  counting.list_undeleted(orig_task_list, deleted_tasks)
    
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
  from util.misc import slugify
  new_name = slugify(new_name)
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
  
def archive_tasks(task_list):
  archived_tasks = []
  for task in get_completed_tasks(task_list):
    archived_tasks.append(task)
    
  def txn():
    for task in archived_tasks:
      task.archived = True
      task.put()
      
    task_list.active_tasks_count -= len(archived_tasks)
    task_list.archived_tasks_count += len(archived_tasks)
    task_list.put()
  
  db.run_in_transaction(txn)
  counting.list_archived(task_list, archived_tasks)
  from tasks_data.tasks import set_tasks_memcache
  set_tasks_memcache(task_list, None)
  
  return archived_tasks
  
def unarchive_tasks(task_list, archived_tasks):
  def txn():
    for task in archived_tasks:
      task.archived = False
      task.put()
      
    task_list.active_tasks_count += len(archived_tasks)
    task_list.archived_tasks_count -= len(archived_tasks)
    task_list.put()

  db.run_in_transaction(txn)
  counting.list_unarchived(task_list, archived_tasks)
  from tasks_data.tasks import set_tasks_memcache
  set_tasks_memcache(task_list, None)
  
  
  
  