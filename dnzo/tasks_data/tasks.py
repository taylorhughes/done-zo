
from google.appengine.ext import db

from tasks_data.models import Task, Undo

from tasks_data.users import save_user
from tasks_data.misc import save_project, save_contexts

#
#  This specifies how long the maximum indexized value can be.
#  This essentially limits the maximum number of records to 
#  MAX_INDEX_LENGTH index records per unique indexed value,
#  but also restricts the resultset from index queries to results
#  appearing in the first MAX_INDEX_LENGTH characters of the value.
#
MAX_INDEX_LENGTH = 50
    
  
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

    save_user(user)
    
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

    save_user(user)

    undo.put()

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

    save_user(user)
    
  db.run_in_transaction(txn, task, task_list)

def update_task_with_params(user, task, params):
  from util.misc import param, slugify
  
  if param('complete', params) == "true":
    task.complete = True
    from datetime import datetime
    task.completed_at = datetime.utcnow()
  else:
    task.complete = False
    task.completed_at = None
  
  task.body = param('body', params, '')
  
  raw_project = param('project', params, None)
  if raw_project is not None:
    raw_project = raw_project.strip()
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
    raw_contexts = re.split(r'[,;\s]+', raw_contexts)
    for raw_context in raw_contexts:
      slug = slugify(raw_context)
      if len(slug) > 0:
        task.contexts.append(slug)
  
  raw_due_date = param('due_date', params, None)
  if raw_due_date is not None:
    from util.parsing import parse_date
    task.due_date = None
    task.due_date = parse_date(raw_due_date, user.timezone_offset_mins)
    
  
