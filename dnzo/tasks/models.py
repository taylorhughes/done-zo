#from django.db import models
from google.appengine.ext import db
from google.appengine.api import users

class TasksUser(db.Model):  
  short_name = db.StringProperty(required=True)
  user       = db.UserProperty()
    
class TaskList(db.Model):
  short_name = db.StringProperty()
  name       = db.StringProperty()
  owner      = db.ReferenceProperty(TasksUser, collection_name='task_lists')
  deleted    = db.BooleanProperty(default=False)
  
  def editing():
    def fset(self, value):
      self.__editing = value
    def fget(self):
      return self.__editing
    return locals()
  editing = property(**editing())

class Project(db.Model):
  name       = db.StringProperty(required=True)
  short_name = db.StringProperty()
  created_at = db.DateTimeProperty(auto_now_add=True)
  owner      = db.ReferenceProperty(TasksUser, collection_name='projects')
    
class Context(db.Model):
  name       = db.StringProperty(required=True)
  created_at = db.DateTimeProperty(auto_now_add=True)
  owner      = db.ReferenceProperty(TasksUser, collection_name='contexts')
  
  def tasks(self, fetch=50):
    result = Task.gql("WHERE contexts=:context AND user=:user",
                      context=self.short_name, user=self.owner)
    return result.fetch(fetch)

class Task(db.Model):
  created_at = db.DateTimeProperty(auto_now_add=True)
  body       = db.StringProperty()
  # Whether or not the task is complete
  complete   = db.BooleanProperty(default=False)
  # For a complete task, whether it is shown in the list
  purged     = db.BooleanProperty(default=False)
  # Need this so we can filter it out in the archived tasks list
  deleted    = db.BooleanProperty(default=False)
  due_date   = db.DateTimeProperty()
  contexts   = db.StringListProperty()
  project    = db.ReferenceProperty(Project, collection_name='tasks')
  owner      = db.ReferenceProperty(TasksUser, collection_name='tasks')
  task_list  = db.ReferenceProperty(TaskList, collection_name='tasks')

  def editing():
    def fset(self, value):
      self.__editing = value
    def fget(self):
      return self.__editing
    return locals()
  editing = property(**editing())

  def __init__(self, *args, **kwargs):
    self.editing = False
    db.Model.__init__(self, *args, **kwargs)

class Undo(db.Model):
  task_list     = db.ReferenceProperty(TaskList, collection_name='undos')
  owner         = db.ReferenceProperty(TasksUser, collection_name='undos')
  created_at    = db.DateTimeProperty(auto_now_add=True)

  list_deleted  = db.BooleanProperty(default=False)
  deleted_tasks = db.ListProperty(db.Key)
  purged_tasks  = db.ListProperty(db.Key)

  def find_deleted(self):
    deleted = []
    for key in self.deleted_tasks:
      deleted.append(db.get(key))
    return deleted
    
  def find_purged(self):
    purged = []
    for key in self.purged_tasks:
      purged.append(db.get(key))
    return purged
    
  def undo(self):
    for task in self.find_deleted():
      task.task_list = self.task_list
      task.deleted = False
      task.put()
    for task in self.find_purged():
      task.purged = False
      task.put()
    if self.list_deleted:
      self.task_list.deleted = False
      self.task_list.put()
      
    self.delete()

  def finish(self):
    for task in self.find_deleted():
      task.delete()
    self.delete()

















