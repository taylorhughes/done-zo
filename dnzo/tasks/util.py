from google.appengine.api.users import get_current_user

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect

from tasks.errors import *
from tasks.models import *

import datetime
from time import strptime

import logging
import re

def access_error_redirect():
  logging.error("Shit! Access error.")
  return HttpResponseRedirect('/')
  
def is_ajax(request):
  ajax_header = 'HTTP_X_REQUESTED_WITH'
  return ajax_header in request.META and request.META[ajax_header] == 'XMLHttpRequest'
  
def urlize(title):
  title = title.lower()
  title = re.sub(r'[^a-z0-9\s]', '', title)
  title = re.sub(r'\s+', '_',  title)
  return title
  
def is_urlized(string):
  return re.search(r'^[a-z0-9_-]+$', string)
  
def get_dnzo_user():
  # TODO: implement caching here
  return TasksUser.gql('WHERE user=:user', user=get_current_user()).get()
  
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
RE_DATE     = re.compile(r'^(\d{1,2})\D+(\d{1,2})(\D+(\d{1,4}))?$')

def parse_date(date_string):
  if not date_string:
    return None
    
  date_string = date_string.strip()
  if len(date_string) == 0:
    return None
  
  match = RE_DATE.match(date_string)
  if match:
    m, d, z, y = match.groups()
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


    