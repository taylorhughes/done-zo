
from google.appengine.ext import webapp

from tasks_data.users import get_dnzo_user

import environment

class BaseAPIRequestHandler(webapp.RequestHandler):
  def json_response(self, *args, **kwargs):
    from django.utils import simplejson as json
    response_body = json.dumps(kwargs)
    self.generate(response_body)

  def generate(self, response):
    self.response.out.write(response)

  def login_required(self):
    self.json_response(error="You must log in first.")

class TasksHandler(BaseAPIRequestHandler):
  def get(self):
    """Return all tasks, optionally filtered on various querystring parameters."""
    dnzo_user = get_dnzo_user()
    if not dnzo_user:
      self.login_required()
      return
  
    from tasks_data.models import Task
    data = {
      'tasks': map(lambda t: t.to_dict(), Task.all())
    }
    
    self.json_response(**data)
  
  def post(self):
    """Create a new task with the JSONized input and return the 
    newly created task as a JSON object."""
    pass
    
class TaskHandler(BaseAPIRequestHandler):
  def get(self, task_id=None):
    dnzo_user = get_dnzo_user()
    if not dnzo_user:
      self.login_required()
      return
    
    from tasks_data.models import Task
    task = Task.get_by_id(int(task_id), parent=dnzo_user)
    
    if not task:
      self.error(404)
    else:
      self.json_response(task=task.to_dict())
      
  def delete(self):
    """Deletes a given task."""
    pass
    
  def put(self):
    """Modify the attributes of an existing task."""
    pass
    