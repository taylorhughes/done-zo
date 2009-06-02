# coding=utf-8

from google.appengine.api.users import create_logout_url, create_login_url, get_current_user, is_current_user_admin

from django.core.urlresolvers import reverse as reverse_url
from django.shortcuts import render_to_response

from tasks.redirects import default_list_redirect, most_recent_redirect

from tasks_data.users import get_dnzo_user

import environment

def welcome(request):
  dnzo_user = get_dnzo_user()
  if dnzo_user:
    return most_recent_redirect(dnzo_user)

  nickname = None
  current_user = get_current_user()
  if current_user:
    nickname = current_user.nickname()
  
  return render_to_response("public/index.html", {
    'nickname': nickname,
    'logout_url': create_logout_url('/'),
    'login_url': create_login_url(reverse_url('tasks.views.redirect')),
    'is_development': environment.IS_DEVELOPMENT
  })
  
def closed(request):
  nickname = None
  current_user = get_current_user()
  if current_user:
    nickname = current_user.nickname()
  
  return render_to_response("public/signup/closed.html", {
    'nickname': nickname,
    'logout_url': create_logout_url('/'),
    'is_development': environment.IS_DEVELOPMENT
  })

def signup(request):
  from django.core.urlresolvers import reverse as reverse_url
  from django.http import HttpResponseRedirect
  
  current_user = get_dnzo_user()
  if current_user:
    return HttpResponseRedirect(reverse_url('tasks.views.redirect'))
  
  from tasks_data.misc import get_invitation_by_address
  from tasks_data.users import create_user
  from tasks_data.runtime_settings import get_setting
  
  current_user = get_current_user()
  allowed      = False
  invitation   = None
  
  if get_setting('registration_open'):
    allowed = True
  elif is_current_user_admin():
    allowed = True
  else:
    invitation = get_invitation_by_address(current_user.email())
    allowed = invitation is not None
  
  if not allowed:
    return HttpResponseRedirect(reverse_url('public.views.closed'))

  from tasks_data.models import TasksUser
  from tasks_data.tasks import DEFAULT_TASKS
  from tasks_data.task_lists import DEFAULT_LIST_NAME
  
  new_user = create_user(current_user, DEFAULT_LIST_NAME, DEFAULT_TASKS)
  
  if invitation:
    from datetime import datetime
    invitation.registered_at = datetime.now()
    invitation.put()
  
  return default_list_redirect(new_user)

  
  
