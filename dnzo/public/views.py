from google.appengine.api.users import create_logout_url, get_current_user, is_current_user_admin

from django.shortcuts import render_to_response

from tasks.redirects import default_list_redirect

from tasks_data.users import get_dnzo_user

import environment

DEFAULT_LIST_NAME = 'Tasks'

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
    'logout_url': create_logout_url('/'),
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
  from tasks_data.task_lists import add_task_list
  
  current_user = get_current_user()
  invitation = get_invitation_by_address(current_user.email())
  if not invitation and not is_current_user_admin():
    return HttpResponseRedirect(reverse_url('public.views.closed'))

  from tasks_data.models import TasksUser
  
  new_user = TasksUser(user=current_user)
  new_user.put()
  
  if invitation:
    from datetime import datetime
    invitation.registered_at = datetime.now()
    invitation.put()
  
  # Create a default new list for this user
  tasks_list = add_task_list(new_user, DEFAULT_LIST_NAME)
  
  return default_list_redirect(new_user)

def handler404(request):
  return render_to_response("404.html")
  
def handler500(request):
  return render_to_response("500.html")
  
  
