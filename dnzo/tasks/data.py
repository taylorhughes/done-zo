#
#  If we've got a "model" layer in the MVC pattern, this is it.
#  This collection of methods retrieves things from the database
#  and also performs (or will perform) caching when necessary.
#

from google.appengine.api.users import get_current_user

from tasks.errors import *
from tasks.models import *
from util.misc import urlize, format_for_index, zpad

from datetime import datetime
import logging
import re

### USERS ###

def users_equal(a,b):
  if a is None and b is None:
    return True
  if a is None or b is None:
    return False
  if a.is_saved() and b.is_saved():
    return a.key().id_or_name() == b.key().id_or_name()
  return False
  
def get_dnzo_user(name=None):
  if name:
    return TasksUser.get_by_key_name(TasksUser.name_to_key_name(name))
  else:
    return TasksUser.gql('WHERE user=:user', user=get_current_user()).get()
  
def username_available(name):
  return not get_dnzo_user(name=name)         
  
def verify_current_user(short_name):
  user = get_dnzo_user()
  if not user or short_name != user.short_name:
    raise AccessError, 'Attempting to access wrong username'
  return user


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
    user.lists_count += 1
    user.put()
    return short_name
    
  short_name = db.run_in_transaction(txn, user, list_name)
  
  return get_task_list(user, short_name)

def delete_task_list(task_list):
  def txn(task_list, deleted_tasks, undo):
    # Make sure we do not double count
    task_list = db.get(task_list.key())
    if task_list.deleted:
      return 
      
    task_list.deleted = True
    task_list.put()
    
    for task in deleted_tasks:
      task = db.get(task.key())
      if not task.deleted:
        task.deleted = True
        task.put()
        undo.deleted_tasks.append(task.key())
    
    user = task_list.parent()
    user.tasks_count -= len(undo.deleted_tasks)
    user.lists_count -= 1
    user.put()
    
    undo.put()
    
  deleted_tasks = Task.gql("WHERE task_list=:list AND archived=:archived",
                           list=task_list, archived=False).fetch(100)
  undo = Undo(task_list=task_list, parent=task_list.parent())
  undo.list_deleted = True
  
  db.run_in_transaction(txn, task_list, deleted_tasks, undo)
  
  return undo
  
def undelete_task_list(task_list):
  def txn(task_list):
    task_list = db.get(task_list.key())
    if not task_list.deleted:
      return
      
    task_list.deleted = False
    task_list.put()
    
    user = task_list.parent()
    user.lists_count += 1
    user.put()

  db.run_in_transaction(txn, task_list)
  
def get_task_lists(user, limit=10):
  query = TaskList.gql(
    'WHERE ANCESTOR IS :user AND deleted=:deleted ORDER BY name ASC', 
    user=user, deleted=False
  )
  return query.fetch(limit)
  
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

def save_task(task):
  if not task.is_saved():
    save_uncounted_task(task)
  else:
    task.put()
  
  if task.project_index:
    save_project(task.parent(), task.project)
  
def undelete_task(task):
  task.deleted = False
  save_uncounted_task(task)
  
def save_uncounted_task(task):
  def txn(task):
    task.put()
    
    user = task.parent()
    user.tasks_count += 1
    user.save()
    
  db.run_in_transaction(txn, task)

def delete_task(task):
  def txn(task, undo):
    task.deleted = True
    task.task_list = None
    task.put()
    
    user = task.parent()
    user.tasks_count -= 1
    user.put()

    undo.put()

  undo = Undo(task_list=task.task_list, parent=task.parent())
  undo.deleted_tasks.append(task.key())
      
  db.run_in_transaction(txn, task, undo)

  return undo
  

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
    project.last_used_at = datetime.now()
    project.put()
    
  return project
  
def create_project(user, project_name):
  def txn(user, project):
    project.put()
    name = format_for_index(project.name)
    while len(name) > 0:
      key_name = IndexedProjectName.name_to_key_name(name)
      index    = IndexedProjectName.get_by_key_name(key_name, parent=user)
      if not index:
        index  = IndexedProjectName(parent=user, key_name=key_name, index=name)
        
      index.projects.append(project.name)
      index.put()
      # Do this for "name", "ame", "me" and "e"
      name = name[1:]
    
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
  indexed_name = format_for_index(project_name)
  
  indexes = IndexedProjectName.gql(
    "WHERE index >= :start AND index < :end AND ANCESTOR IS :user",
    start=indexed_name, end=zpad(indexed_name), user=user
  )
  
  project_names = set()
  for index in indexes:
    for project_name in index.projects:
      project_names.add(project_name)
  
  if len(project_names) > 0:
    bound_vars = {'user': user}
    # Having to do this sucks
    while len(project_names) > 0:
      key = 'name_' + str(len(project_names))
      bound_vars[key] = project_names.pop()
    
    placeholders = map(lambda k : ":" + k, bound_vars.keys())
    placeholders = ', '.join(placeholders)
    projects = Project.gql(
      'WHERE name IN (' + placeholders + ') AND ANCESTOR IS :user ' +
      'ORDER BY last_used_at DESC',
      **bound_vars
    ).fetch(limit)
    
  else:
    projects = []
  
  return projects
  
def get_project_by_index(user, project_index):
  project = Project.gql(
    'WHERE ANCESTOR IS :user AND short_name=:project_index ' + 
    'ORDER BY last_used_at DESC',
    user=user, project_index=project_index
  ).get()
  
  if project:
    return project.name
  return None
  
  
### UNDOS ###

def do_undo(undo):
  for task in undo.find_deleted():
    task.task_list = undo.task_list
    undelete_task(task)
    
  for task in undo.find_archived():
    task.archived = False
    task.put()
    
  if undo.list_deleted:
    undelete_task_list(undo.task_list)
    
  undo.delete()

  
