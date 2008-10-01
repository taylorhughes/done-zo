from google.appengine.api.users import get_current_user

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse as reverse_url

from tasks.errors import *
from tasks.models import *

import datetime
from time import strptime

import logging
import re

COOKIE_STATUS = 'dnzo-status'
COOKIE_UNDO   = 'dnzo-undo'

def users_equal(a,b):
  if a is None and b is None:
    return true
  if a is None or b is None:
    return false
  return a.key().id() == b.key().id()

def access_error_redirect():
  logging.error("Shit! Access error.")
  return HttpResponseRedirect('/')

def default_list_redirect(user):
  default_list = get_task_lists(user,1)
  if default_list and len(default_list) > 0:
    return HttpResponseRedirect(reverse_url('tasks.views.tasks_index',args=[user.short_name,default_list[0].short_name]))
  else:
    logging.error("Shit! Somehow the user does not have any task lists.")
    return HttpResponseRedirect(reverse_url('tasks.views.lists_index'))

def is_ajax(request):
  ajax_header = 'HTTP_X_REQUESTED_WITH'
  return ajax_header in request.META and request.META[ajax_header] == 'XMLHttpRequest'
  
def urlize(title):
  title = title.lower().strip()
  title = re.sub(r'[^a-z0-9\s]', '', title)
  title = re.sub(r'\s+', '_',  title)
  return title
  
def is_urlized(string):
  return re.search(r'^[a-z0-9_-]+$', string)
  
def get_dnzo_user():
  # TODO: implement caching here
  return TasksUser.gql('WHERE user=:user', user=get_current_user()).get()
  
def get_task_list(user, task_list):
  query = TaskList.gql(
    'WHERE owner=:user AND short_name=:short_name', 
    user=user, short_name=task_list
  )
  return query.get()
                                      
def get_task_lists(user, limit=10):
  query = TaskList.gql(
    'WHERE owner=:user AND deleted=:deleted ORDER BY short_name ASC', 
    user=user, deleted=False
  )
  return query.fetch(limit)
  
def verify_current_user(short_name):
  user = get_dnzo_user()
  if not user or short_name != user.short_name:
    raise AccessError, 'Attempting to access wrong username'
  return user

def param(name, collection, default=None):
  if name in collection:
    return collection[name].strip()
  return default

RE_TODAY    = re.compile(r'^today$', re.I)
RE_TOMORROW = re.compile(r'^tom{1,2}or{1,2}ow$', re.I)
RE_DAY      = re.compile(r'^(mon|tue|wed|thu|fri|sat|sun)\w*$', re.I)
RE_DATE     = re.compile(r'^(\d{1,2})\D+(\d{1,2})(?:\D+(\d{1,4}))?$')

def parse_date(date_string):
  if not date_string:
    return None
    
  date_string = date_string.strip()
  if len(date_string) == 0:
    return None
  
  match = RE_DATE.match(date_string)
  if match:
    m, d, y = match.groups()
    m = int(m)
    d = int(d)
    if y:
      y = int(y)
      if y < 100:
        y += 2000
      elif y < 2000:
        y = None
        
    if not y:
      y = datetime.datetime.now().timetuple()[0]
      if datetime.datetime(y, m, d) < datetime.datetime.now():
        y += 1
      
    return datetime.datetime(y, m, d)
    
  if RE_TODAY.match(date_string):
    return today_datetime()
    
  if RE_TOMORROW.match(date_string):
    return today_datetime() + datetime.timedelta(days=1)
    
  match = RE_DAY.match(date_string)
  if match:
    day = match.groups()[0].lower()
    next_day = today_datetime() + datetime.timedelta(days=1)
    while next_day.strftime("%a").lower() != day:
      next_day += datetime.timedelta(days=1)
    return next_day
  
  return None
    
def today_datetime():
  return datetime.datetime(*datetime.datetime.now().timetuple()[0:3])


    