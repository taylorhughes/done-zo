
from google.appengine.ext import db

from tasks_data.models import Task

from tasks_data.users import save_user
from tasks_data.misc import save_project, save_contexts


# This is actually a limitation of the datastore:
#   string types can only be 500 characters.
MAX_BODY_LENGTH    = 500

# This is mostly a factor of what it will make the UI 
# look like and how long and unwieldy URLs will get
MAX_PROJECT_LENGTH = 30
MAX_CONTEXT_LENGTH = 30

# Maximum number of undeleted, unarchived tasks for a list.
MAX_ACTIVE_TASKS   = 100
  
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
    
  save_user(user)
  
def add_task(task):
  def txn(task, task_list):
    if task.is_saved():
      return
    
    task.put()
    
    task_list.active_tasks_count += 1
    task_list.put()
  
  task_list = task.task_list
  if task_list.active_tasks_count < MAX_ACTIVE_TASKS:
    db.run_in_transaction(txn, task, task_list)

def delete_task(user, task):
  def txn(task):
    task = db.get(task.key())
    if task.deleted:
      return

    task_list = task.task_list
    task_list.active_tasks_count -= 1
    task_list.put()
    
    task.deleted = True
    task.task_list = None
    task.put()
      
  db.run_in_transaction(txn, task)

def undelete_task(task, task_list):
  def txn(task, task_list):
    task = db.get(task.key())
    was_deleted = task.deleted
    task.deleted = False
    task.task_list = task_list
    task.put()
    
    if not was_deleted:
      return
    
    task_list = task.task_list
    task_list.active_tasks_count += 1
    task_list.put()
    
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
  
  raw_due_date = param('due_date', params, None)
  if raw_due_date is not None:
    from util.human_time import parse_date
    task.due_date = None
    task.due_date = parse_date(raw_due_date, user.timezone_offset_mins)
    
  
