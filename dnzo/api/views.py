from google.appengine.ext import webapp
from tasks_data.users import get_dnzo_user

def dnzo_login_required(fn):
  """Decorator for a BaseAPIRequestHelper to make it require a DNZO login."""
  def logged_in_wrapper(self, *args):
    dnzo_user = get_dnzo_user()
    if not dnzo_user:
      self.login_required()
    else:
      fn(self, dnzo_user, *args)
  return logged_in_wrapper
  
class BaseAPIRequestHandler(webapp.RequestHandler):
  def json_response(self, *args, **kwargs):
    from django.utils import simplejson as json
    response_body = json.dumps(kwargs)
    self.generate(response_body)

  def generate(self, response):
    self.response.out.write(response)

  def login_required(self):
    self.error(403)
    self.json_response(error="Login required.")
    
  def not_found(self):
    self.error(404)
    self.json_response(error="Not found")

class TasksHandler(BaseAPIRequestHandler):
  @dnzo_login_required
  def get(self, dnzo_user):
    """Return all tasks, optionally filtered on various querystring parameters."""
    from tasks_data.models import Task
    data = {
      'tasks': map(lambda t: t.to_dict(), Task.all())
    }
    
    self.json_response(**data)
  
  @dnzo_login_required
  def post(self, dnzo_user):
    """Create a new task with the JSONized input and return the 
    newly created task as a JSON object."""
    pass

class TaskHandler(BaseAPIRequestHandler):
  def operates_on_task(fn):
    """Decorator for a TaskHandler task to """
    @dnzo_login_required
    def task_wrapper(self, dnzo_user, task_id, *args):
      from tasks_data.models import Task
      task = Task.get_by_id(int(task_id), parent=dnzo_user)
      if not task:
        self.not_found()
      else:
        fn(self, dnzo_user, task, *args)
    return task_wrapper
  
  @operates_on_task
  def get(self, dnzo_user, task):
    self.json_response(task=task.to_dict())
  
  @operates_on_task
  def delete(self, dnzo_user, task):
    """Deletes a given task."""
    pass
    
  @operates_on_task
  def put(self, dnzo_user, task):
    """Modify the attributes of an existing task."""
    pass
    
class TaskListHandler(BaseAPIRequestHandler):
  @dnzo_login_required
  def get(self, task_list_name):
    """Returns the name of a task and how many tasks are in it."""
    pass
  
  def delete(self, task_list_name):
    """Deletes a task list."""
    pass
  
class TaskListsHandler(BaseAPIRequestHandler):
  def get(self):
    """Returns a list of all the task lists in the system."""
    pass
  
  def post(self):
    """Creates a new task list."""
    pass
  
  