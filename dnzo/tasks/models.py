#from django.db import models
from google.appengine.ext import db
from google.appengine.api import users

class TasksUser(db.Model):
  user          = db.UserProperty()
  short_name    = db.StringProperty()
  
  tasks_count   = db.IntegerProperty(default=0)
  lists_count   = db.IntegerProperty(default=0)
  
  @classmethod
  def name_to_key_name(self,name):
    return "user(%s)" % name
    
class TaskList(db.Model):
  name          = db.StringProperty()
  short_name    = db.StringProperty()
  deleted       = db.BooleanProperty(default=False)
  
  @classmethod
  def name_to_key_name(self,name):
    return "list(%s)" % name

class Task(db.Model):
  task_list     = db.ReferenceProperty(TaskList, collection_name='tasks')
  created_at    = db.DateTimeProperty(auto_now_add=True)
  
  complete      = db.BooleanProperty(default=False)
  
  project_index = db.StringProperty()
  project       = db.StringProperty()

  contexts      = db.StringListProperty()

  due_date      = db.DateTimeProperty()
  body          = db.StringProperty()
  
  # For a complete task, whether it is shown in the list
  archived      = db.BooleanProperty(default=False)
  # Need this so we can filter it out in the archived tasks list
  deleted       = db.BooleanProperty(default=False)

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
  task_list      = db.ReferenceProperty(TaskList, collection_name='undos')
  created_at     = db.DateTimeProperty(auto_now_add=True)

  list_deleted   = db.BooleanProperty(default=False)
  deleted_tasks  = db.ListProperty(db.Key)
  archived_tasks = db.ListProperty(db.Key)

  def find_deleted(self):
    deleted = []
    for key in self.deleted_tasks:
      deleted.append(db.get(key))
    return deleted
    
  def find_archived(self):
    archived = []
    for key in self.archived_tasks:
      archived.append(db.get(key))
    return archived





