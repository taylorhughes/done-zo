from google.appengine.api import users

from public.views import DEFAULT_LIST_NAME, DEFAULT_TASKS

from tasks_data.models import *
from tasks_data.users import create_user

MODELS = (Task, TaskList, TasksUser, Project, Context, Undo)
DUMMY_USER_ADDRESS = 'ima@user.com'

def destroy_fixtures():
  for klass in MODELS:
    for obj in klass.all():
      obj.delete()
      
def fixture_user():
  return users.User(DUMMY_USER_ADDRESS)

def fixture_dnzo_user():
  return get_dnzo_user_by_email(DUMMY_USER_ADDRESS)
  
def create_fixtures():
  create_user(fixture_user(), DEFAULT_LIST_NAME, DEFAULT_TASKS)
      
def setup_fixtures():
  destroy_fixtures()
  create_fixtures()