#from django.db import models
from google.appengine.ext import db
from google.appengine.api import users

class TasksUser(db.Model):  
  short_name = db.StringProperty(required=True)
  user       = db.UserProperty()
  @property
  def tasks_url(self):
    return "/%s/" % self.short_name
    
class TaskList(db.Model):
  short_name = db.StringProperty()
  name       = db.StringProperty()
  owner      = db.ReferenceProperty(TasksUser, collection_name='task_lists')
  
  def editing():
    def fset(self, value):
      self.__editing = value
    def fget(self):
      return self.__editing
    return locals()
  editing = property(**editing())
  
  @property
  def url(self):
    return "/%s/%s/" % (self.owner.short_name, self.short_name)

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
  due_date   = db.DateTimeProperty()
  contexts   = db.StringListProperty()
  project    = db.ReferenceProperty(Project, collection_name='tasks')
  owner      = db.ReferenceProperty(TasksUser, collection_name='tasks')
  task_list  = db.ReferenceProperty(TaskList, collection_name='tasks')

  @property
  def url(self):
    tasks_url = "/%s/%s/" % (self.owner.short_name, self.task_list.short_name)
    if self.is_saved():
      return tasks_url + self.key()
    return tasks_url

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
  created_at    = db.DateTimeProperty(auto_now_add=True)

  deleted_tasks = db.StringListProperty()
  purged_tasks  = db.StringListProperty()

  def find_deleted(self):
    deleted = []
    for key in self.deleted_tasks:
      deleted.append(db.get(db.Key(key)))
    return deleted
    
  def find_purged(self):
    purged = []
    for key in self.purged_tasks:
      purged.append(db.get(db.Key(key)))
    return purged
    
  def undo(self):
    for task in self.find_deleted():
      task.task_list = self.task_list
      task.put()
    for task in self.find_purged():
      task.purged = False
      task.put()

  def finish(self):
    for task in self.find_deleted():
      task.delete()

















