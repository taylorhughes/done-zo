import logging

from google.appengine.api import users, memcache

from tasks_data.task_lists import DEFAULT_LIST_NAME
from tasks_data.tasks import DEFAULT_TASKS

from tasks_data.models import *
from tasks_data.users import create_user, get_dnzo_user_by_email

MODELS = (Task, TaskList, Project, Context, Undo)

DUMMY_USER_ADDRESS = 'ima@user.com'
ANOTHER_USER_ADDRESS = 'another@user.com'
      
def fixture_user():
  return users.User(DUMMY_USER_ADDRESS)

def fixture_dnzo_user():
  return get_dnzo_user_by_email(DUMMY_USER_ADDRESS)
  
def create_fixtures():
  create_user(fixture_user(), DEFAULT_LIST_NAME, DEFAULT_TASKS)
  # Create another user so we have some other stuff in the datastore to *not* see
  create_user(users.User(ANOTHER_USER_ADDRESS), DEFAULT_LIST_NAME, DEFAULT_TASKS)
      
def setup_fixtures():
  memcache.flush_all()
  create_fixtures()