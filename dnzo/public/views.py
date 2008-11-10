from google.appengine.api.users import create_logout_url, get_current_user

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse as reverse_url

from tasks.errors    import *
from tasks.data      import *
from tasks.redirects import *
from util.misc       import *

import environment
import logging

DEFAULT_LIST_NAME = 'Tasks'
MINIMUM_USER_URL_LENGTH = 5

def welcome(request):
  dnzo_user = get_dnzo_user()
  if dnzo_user:
    return default_list_redirect(dnzo_user)
    
  return render_to_response("index.html", {
    'signed_in': (get_current_user() is not None)
  })

def availability(request):
  name = param('name', request.GET, '')
  message = username_invalid(name)
  
  if is_ajax(request):
    return render_to_response('signup/availability_ajax.html', {
      'unavailable': message is not None,
      'message':     message
    })
  else:
    return HttpResponseRedirect(reverse_url('tasks.views.signup'))

def signup(request):
  current_user = get_dnzo_user()
  if current_user:
    return default_list_redirect(current_user)
  
  current_user = get_current_user()

  if request.method == 'POST':
    name = param('name',request.POST)
    message = username_invalid(name)

    if not message:
      new_user = TasksUser(
        key_name=TasksUser.name_to_key_name(name), 
        user=current_user,
        short_name = name
      )
      new_user.put()
      
      # Create a default new list for this user
      tasks_list = add_task_list(new_user, DEFAULT_LIST_NAME)
      
      return default_list_redirect(new_user)

  else:
    message = None
    original = urlize(current_user.nickname())
    i, name = 1, original
    while not username_available(name):
      name = "%s_%s" % (original, i)
      i += 1

  return render_to_response('signup/index.html', {
    'short_name':  name,
    'unavailable': message is not None,
    'message':     message
  })
  
  
def username_invalid(new_name):
  message = None
    
  if not is_urlized(new_name):
    message = 'URLs can only contain lowercase letters, numbers, underscores and hyphens.'
    urlized = urlize(new_name)
    if len(urlized) >= MINIMUM_USER_URL_LENGTH:
      message += " How about &ldquo;%s&rdquo;?" % urlized
    
  elif not len(new_name) >= MINIMUM_USER_URL_LENGTH:
    message = 'URLs must be at least %s characters long.' % MINIMUM_USER_URL_LENGTH
    
  elif not username_available(new_name):
    message = 'Unfortunately, that URL has been taken.'
    
  return message
  