#from django.db import models
from google.appengine.ext import db
from google.appengine.api import users

from django.db.models import permalink

class TasksUser(db.Model):
  user          = db.UserProperty()
    
  # Settings
  hide_project  = db.BooleanProperty(default=False)
  hide_contexts = db.BooleanProperty(default=False)
  hide_due_date = db.BooleanProperty(default=False)
  
  # Timezone offset in minutes from UTC/GMT
  # CST in the winter = 360, aka UTC/GMT -600
  timezone_offset_mins = db.IntegerProperty(default=0)
  
  # Last URI the user visited
  most_recent_uri = db.StringProperty()
  
  # Counts
  tasks_count   = db.IntegerProperty(default=0)
  lists_count   = db.IntegerProperty(default=0)
  
  @permalink
  def get_absolute_url(self):
    return('tasks.views.redirect')
    
class TaskList(db.Model):
  name          = db.StringProperty()
  short_name    = db.StringProperty()
  deleted       = db.BooleanProperty(default=False)
  
  @classmethod
  def name_to_key_name(self,name):
    return "list(%s)" % name
    
  @permalink
  def get_absolute_url(self):
    return ('tasks.views.list_index', None, {
      'task_list_name': self.short_name
    })

class Task(db.Model):
  task_list     = db.ReferenceProperty(TaskList, collection_name='tasks')
  created_at    = db.DateTimeProperty(auto_now_add=True)
  
  complete      = db.BooleanProperty(default=False)
  completed_at  = db.DateTimeProperty()
  
  project_index = db.StringProperty()
  project       = db.StringProperty()

  contexts      = db.StringListProperty()

  due_date      = db.DateTimeProperty()
  body          = db.StringProperty()
  
  # For a complete task, whether it is shown in the list
  archived      = db.BooleanProperty(default=False)
  # Need this so we can filter it out in the archived tasks list
  deleted       = db.BooleanProperty(default=False)

  @permalink
  def get_absolute_url(self):
    return ('tasks.views.task', None, {
      'task_id': self.key().id()
    })

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
  
class Project(db.Model):
  @classmethod
  def name_to_key_name(self,name):
    return "project(%s)" % name
  name         = db.StringProperty()
  short_name   = db.StringProperty()
  created_at   = db.DateTimeProperty(auto_now_add=True)

#
#  Contains pieces of project names that reference projects
#
class ProjectIndex(db.Model):
  index        = db.StringProperty()
  name         = db.StringProperty()
  project      = db.ReferenceProperty(Project, collection_name='indexes')
  last_used_at = db.DateTimeProperty(auto_now_add=True)

class Context(db.Model):
  @classmethod
  def name_to_key_name(self,name):
    return "context(%s)" % name
  name         = db.StringProperty()
  last_used_at = db.DateTimeProperty(auto_now_add=True)

class Undo(db.Model):
  task_list      = db.ReferenceProperty(TaskList, collection_name='undos')
  created_at     = db.DateTimeProperty(auto_now_add=True)

  list_deleted   = db.BooleanProperty(default=False)
  deleted_tasks  = db.ListProperty(db.Key)
  archived_tasks = db.ListProperty(db.Key)

  return_uri     = db.StringProperty()

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

  @permalink
  def get_absolute_url(self):
    return ('tasks.views.undo', None, {
      'undo_id': self.key().id()
    })

class Invitation(db.Model):
  email_address = db.StringProperty()
  created_at    = db.DateTimeProperty(auto_now_add=True)
  registered_at = db.DateTimeProperty()
  username      = db.StringProperty()
  added_by      = db.UserProperty()

