from google.appengine.ext import webapp
from tasks_data.users import get_dnzo_user
from django.utils import simplejson as json

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
  def __init__(self):
    self.__errored = False
  
  def json_response(self, *args, **kwargs):
    response_body = json.dumps(kwargs)
    if 'error' in kwargs and not self.__errored:
      self.error(500)
    self.generate(response_body)

  def generate(self, response):
    self.response.out.write(response)

  def error(self, *args):
    self.__errored = True
    super(BaseAPIRequestHandler, self).error(*args)

  def login_required(self):
    self.error(403)
    self.json_response(error="Login required.")
    
  def not_found(self):
    self.error(404)
    self.json_response(error="Not found")

class APITasksHandler(BaseAPIRequestHandler):
  @dnzo_login_required
  def get(self, dnzo_user):
    """Return all tasks, optionally filtered on various querystring parameters."""
    from tasks_data.models import Task
    tasks = Task.gql(
      'where ancestor is :user and deleted=:deleted and archived=:archived',
      user=dnzo_user, deleted=False, archived=False
    )

    data = { 'tasks': map(lambda t: t.to_dict(), tasks) }
    
    self.json_response(**data)
  
  @dnzo_login_required
  def post(self, dnzo_user):
    """Create a new task with the JSONized input and return the 
    newly created task as a JSON object."""
    from tasks_data.models import Task
    from tasks_data.tasks import update_task_with_params
    try:
      task = Task(parent=dnzo_user)
      update_task_with_params(dnzo_user, task, self.request)
      task.put()

    except:
      task = None
      
    if not task:
      self.json_response(error="Could not create task!")
    else:
      self.json_response(task=task.to_dict())
    
    
class APITaskHandler(BaseAPIRequestHandler):
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
    from tasks_data.tasks import delete_task
    delete_task(task)
    self.json_response(task=task)
    
  @operates_on_task
  def put(self, dnzo_user, task):
    """Modify the attributes of an existing task."""
    pass
    
class APITaskListHandler(BaseAPIRequestHandler):
  @dnzo_login_required
  def get(self, task_list_name):
    """Returns the name of a task and how many tasks are in it."""
    pass
  
  def delete(self, task_list_name):
    """Deletes a task list."""
    pass
  
class APITaskListsHandler(BaseAPIRequestHandler):
  def get(self):
    """Returns a list of all the task lists in the system."""
    pass
  
  def post(self):
    """Creates a new task list."""
    pass
  
  