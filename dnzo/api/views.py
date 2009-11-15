from google.appengine.ext import webapp
from tasks_data.users import get_dnzo_user
from django.utils import simplejson as json
import logging

def dnzo_login_required(fn):
  """Decorator for a BaseAPIRequestHelper to make it require a DNZO login."""
  def logged_in_wrapper(self, *args):
    from google.appengine.api.users import get_current_user
    dnzo_user = get_dnzo_user()
    
    if not dnzo_user and get_current_user():
      from tasks_data.users import create_user
      dnzo_user = create_user(get_current_user())
    
    if dnzo_user:
      fn(self, dnzo_user, *args)
    else:
      self.login_required()
    
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

  def handle_exception(self, exception, debug_mode):
    if debug_mode:
      super(BaseAPIRequestHandler,self).handle_exception(exception,debug_mode)
    else:
      logging.exception("An exception occurred. Rendered a 500 error message. Yikes!")
      self.error(500)
      self.json_response(error="An unknown error has occurred.")
      
  def error(self, *args):
    self.__errored = True
    super(BaseAPIRequestHandler, self).error(*args)

  def login_required(self):
    self.error(403)
    self.json_response(error="Google login required.")
    
  def not_found(self):
    self.error(404)
    self.json_response(error="Not found")
    
  def bad_request(self, message="Bad request"):
    self.error(400)
    self.json_response(error=message)

class APITasksHandler(BaseAPIRequestHandler):
  @dnzo_login_required
  def get(self, dnzo_user):
    """Return all tasks, optionally filtered on various querystring parameters."""
    from tasks_data.models import Task
    
    updated_since = self.request.get('updated_since', None)
    if updated_since:
      from util.human_time import parse_datetime
      updated_since = parse_datetime(updated_since)
      if not updated_since:
        self.bad_request("Could not parse supplied date.")
        return
    
    task_list_key = self.request.get('task_list', None) 
    task_list = None
    if task_list_key:
      from tasks_data.task_lists import get_task_list
      task_list = get_task_list(dnzo_user, task_list_key)
      if not task_list:
        self.bad_request("Could not find task_list with key '%s'." % task_list_key)
        return
        
    if not (task_list or updated_since):
      self.bad_request("Must supply task_list or updated_since.")
      return

    from tasks_data.tasks import get_tasks
    tasks = get_tasks(dnzo_user, updated_since=updated_since, task_list=task_list)
    
    data = { 'tasks': map(lambda t: t.to_dict(), tasks) }
    
    self.json_response(**data)
  
  @dnzo_login_required
  def post(self, dnzo_user):
    """Create a new task with the JSONized input and return the 
    newly created task as a JSON object."""
    from google.appengine.ext import db
    from tasks_data.models import Task
    from tasks_data.tasks import update_task_with_params, save_task
    from tasks_data.task_lists import get_task_list
  
    task = Task(parent=dnzo_user)
    
    task_list = self.request.get('task_list', None) 
    task_list = task_list and get_task_list(dnzo_user, task_list)
    if task_list:
      task.task_list = task_list
    else:
      self.bad_request("Could not find the specified task list.")
      return
      
    update_task_with_params(dnzo_user, task, self.request)
    save_task(dnzo_user, task)
    # reload task
    task = db.get(task.key())
  
    self.json_response(task=task.to_dict())
    
    
class APIArchivedTasksHandler(BaseAPIRequestHandler):
  @dnzo_login_required
  def get(self, dnzo_user):
    """Return all tasks, optionally filtered on various querystring parameters."""
    from tasks_data.models import Task
    from util.human_time import parse_datetime
        
    start_at = self.request.get('start_at', None)
    end_at = self.request.get('end_at', None)
    if not (start_at and end_at):
      self.bad_request("Must include start_at and end_at for archived tasks.")
      return
    
    start_at = parse_datetime(start_at)
    if not start_at:
      self.bad_request("Could not parse supplied date 'start_at'.")
      return
      
    end_at = parse_datetime(end_at)
    if not end_at:
      self.bad_request("Could not parse supplied date 'end_at'.")
      return
    
    if (start_at > end_at):
      self.bad_request("Invalid range; start_at must come before end_at.")
      return

    from tasks_data.tasks import get_archived_tasks
    tasks = get_archived_tasks(dnzo_user, start_at, end_at)
    
    data = { 'tasks': map(lambda t: t.to_dict(), tasks) }
    
    self.json_response(**data)
    
    
class APITaskHandler(BaseAPIRequestHandler):
  def operates_on_task(fn):
    """Decorator for a TaskHandler task to """
    @dnzo_login_required
    def task_wrapper(self, dnzo_user, task_id, *args):
      from tasks_data.models import Task
      task = Task.get_by_id(int(task_id), parent=dnzo_user)
      if not task or task.deleted:
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
    delete_task(dnzo_user, task)
    self.json_response(task=task.to_dict())
    
  @operates_on_task
  def put(self, dnzo_user, task):
    """Modify the attributes of an existing task."""
    from google.appengine.ext import db
    from tasks_data.tasks import update_task_with_params, save_task

    try:
      # hack to allow form-encoded PUT bodies to be accessed by self.request.get()
      self.request.method = "POST"
      update_task_with_params(dnzo_user, task, self.request)
      
    except AssertionError, strerror:
      self.bad_request(strerror.message)
      return
      
    finally:
      self.request.method = "PUT"
      
    save_task(dnzo_user, task)
    # reload task
    task = db.get(task.key())
    
    self.json_response(task=task.to_dict())

### TASK LISTS ###
  
class APITaskListsHandler(BaseAPIRequestHandler):
  @dnzo_login_required
  def get(self, dnzo_user):
    """Returns a list of all the task lists in the system."""
    from tasks_data.task_lists import get_task_lists
    lists = get_task_lists(dnzo_user, force_reload=True)
    
    self.json_response(task_lists=[l.to_dict() for l in lists])
  
  @dnzo_login_required
  def post(self, dnzo_user):
    """Creates a new task list."""
    from tasks_data.task_lists import add_task_list, get_task_list
    
    task_list_name = self.request.get('task_list_name', None)
    if not task_list_name:
      self.bad_request("Must provide task_list_name to create a new list")
      return
      
    new_list = add_task_list(dnzo_user, task_list_name)
    if not new_list:
      self.bad_request("Could not add the new task list!")
      return
      
    self.json_response(task_list=new_list.to_dict())
    

class APITaskListHandler(BaseAPIRequestHandler):
  def operates_on_task_list(fn):
    """Decorator for a TaskHandler task to """
    @dnzo_login_required
    def task_wrapper(self, dnzo_user, task_list_name, *args):
      from tasks_data.task_lists import get_task_list
      task_list = get_task_list(dnzo_user, task_list_name)
      if not task_list or task_list.deleted:
        self.not_found()
      else:
        fn(self, dnzo_user, task_list, *args)
    return task_wrapper
    
  @operates_on_task_list
  def get(self, dnzo_user, task_list):
    """Returns the name of a task list and how many tasks are in it."""
    self.json_response(task_list=task_list.to_dict())
  
  @operates_on_task_list
  def delete(self, dnzo_user, task_list):
    """Deletes a task list."""
    from tasks_data.task_lists import delete_task_list
    if dnzo_user.lists_count <= 1:
      self.bad_request("User only has one list; cannot delete the last list.")
      return
      
    delete_task_list(dnzo_user, task_list)
    self.json_response(task_list=task_list.to_dict())
  
class APIResetAccountHandler(BaseAPIRequestHandler):
  @dnzo_login_required
  def get(self, dnzo_user):
    import environment
    if environment.IS_PRODUCTION:
      return
    from tasks_data.users import delete_user_and_data
    delete_user_and_data(dnzo_user)  
  
  