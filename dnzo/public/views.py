from google.appengine.api.users import create_logout_url, get_current_user, is_current_user_admin

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse as reverse_url

from tasks.models    import *
from tasks.data      import *
from tasks.redirects import *
from util.misc       import *

from public.data     import *

import environment
import logging
import datetime
import re

DEFAULT_LIST_NAME = 'Tasks'
MINIMUM_USER_URL_LENGTH = 1

def welcome(request):
  dnzo_user = get_dnzo_user()
  if dnzo_user:
    return default_list_redirect(dnzo_user)

  nickname = None
  current_user = get_current_user()
  if current_user:
    nickname = current_user.nickname()
    
  return render_to_response("public/index.html", {
    'nickname': nickname,
    'logout_url': create_logout_url('/')
  })
  
def closed(request):
  return render_to_response("public/signup/closed.html")

def availability(request):
  name = param('name', request.GET, '')
  message = username_invalid(name)
  
  if is_ajax(request):
    return render_to_response('public/signup/availability_ajax.html', {
      'unavailable': message is not None,
      'message':     message
    })
  else:
    return HttpResponseRedirect(reverse_url('public.views.signup'))

def signup(request):
  current_user = get_dnzo_user()
  if current_user:
    return default_list_redirect(current_user)
  
  current_user = get_current_user()
  invitation = get_invitation_by_address(current_user.email())
  if not invitation and not is_current_user_admin():
    return HttpResponseRedirect(reverse_url('public.views.closed'))

  new_user = TasksUser(user=current_user)
  new_user.put()
  
  if invitation:
    invitation.registered_at = datetime.datetime.now()
    invitation.put()
  
  # Create a default new list for this user
  tasks_list = add_task_list(new_user, DEFAULT_LIST_NAME)
  
  return default_list_redirect(new_user)

  

### UTILITY METHODS ###

def username_invalid(new_name):
  message = None
    
  if not len(new_name) >= MINIMUM_USER_URL_LENGTH:
    message = 'URLs must be at least %s character long.' % MINIMUM_USER_URL_LENGTH
    
  elif not is_urlized(new_name):
    message = 'URLs can only contain lowercase letters, numbers, underscores and hyphens.'
    urlized = urlize(new_name)
    if len(urlized) >= MINIMUM_USER_URL_LENGTH:
      message += " How about &ldquo;%s&rdquo;?" % urlized
    
  elif not username_available(new_name):
    message = 'Unfortunately, that URL has been taken.'
    
  return message
  