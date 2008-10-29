#
#  If we've got a "model" layer in the MVC pattern, this is it.
#  This collection of methods retrieves things from the database
#  and also performs (or will perform) caching when necessary.
#

from google.appengine.api.users import get_current_user

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse as reverse_url

from tasks.errors import *
from tasks.models import *
from util.misc import urlize

import logging
import re

def users_equal(a,b):
  if a is None and b is None:
    return True
  if a is None or b is None:
    return False
  if a.is_saved() and b.is_saved():
    return a.key().id() == b.key().id()
  return False

def access_error_redirect():
  # TODO: Redirect to some kind of 5xx access denied error.
  logging.error("Shit! Access error.")
  return HttpResponseRedirect('/')

def default_list_redirect(user):
  '''Redirect a user to his defalt task list.'''
  default_list = get_task_lists(user,1)
  if default_list and len(default_list) > 0:
    return HttpResponseRedirect(reverse_url('tasks.views.list_index',args=[user.short_name,default_list[0].short_name]))
  else:
    logging.error("Shit! Somehow the user does not have any task lists.")
    return HttpResponseRedirect(reverse_url('tasks.views.lists_index'))

def referer_redirect(user, request):
  '''Redirect a user to where he came from. If he didn't come from anywhere,
    refer him to a default location.'''
  if 'HTTP_REFERER' in request.META:
    return HttpResponseRedirect(request.META['HTTP_REFERER'])
  return default_list_redirect(user)
  
def get_dnzo_user(short_name=None):
  if short_name:
    return TasksUser.gql('WHERE short_name=:name', name=short_name).get()
  else:
    return TasksUser.gql('WHERE user=:user', user=get_current_user()).get()
  
def get_task_list(user, task_list_name):
  query = TaskList.gql(
    'WHERE owner=:user AND short_name=:short_name', 
    user=user, short_name=task_list_name
  )
  return query.get()

def get_task_lists(user, limit=10):
  query = TaskList.gql(
    'WHERE owner=:user AND deleted=:deleted ORDER BY short_name ASC', 
    user=user, deleted=False
  )
  return query.fetch(limit)
  
def get_completed_tasks(task_list, limit=100):
  tasks = Task.gql('WHERE task_list=:list AND purged=:purged AND complete=:complete', 
                   list=task_list, purged=False, complete=True)
  return tasks.fetch(limit)
  
def get_context_by_name(user, short_name):
  return Context.gql('WHERE owner=:user AND name=:name', user=user, name=short_name).get()

def get_project_by_name(user, short_name):
  project = Project.gql('WHERE owner=:user AND short_name=:name', 
                               user=user, name=short_name)
  return project.get()
  
def get_new_list_name(user, new_name):
  new_name = urlize(new_name)
  appendage = ''
  i = 1
  while get_task_list(user, new_name + appendage) is not None:
    appendage = "_%s" % i
    i += 1
    
  return new_name + appendage
  
def username_available(name):
  return not get_dnzo_user(short_name=name)         
  
def verify_current_user(short_name):
  user = get_dnzo_user()
  if not user or short_name != user.short_name:
    raise AccessError, 'Attempting to access wrong username'
  return user




    