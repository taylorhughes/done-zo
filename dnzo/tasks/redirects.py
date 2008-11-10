import logging

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse as reverse_url

from tasks.data import *

def access_error_redirect():
  # TODO: Redirect to some kind of 5xx access denied error.
  logging.error("Access error; redirecting to /.")
  return HttpResponseRedirect('/')

def default_list_redirect(user):
  '''Redirect a user to his defalt task list.'''
  default_list = get_task_lists(user,1)
  if default_list and len(default_list) > 0:
    return list_redirect(user, default_list[0])
  else:
    logging.error("Somehow this user does not have any task lists.")
    return HttpResponseRedirect("/")

def list_redirect(user, list):
  return HttpResponseRedirect(
           reverse_url('tasks.views.list_index',
                       args=[user.short_name,list.short_name]
           )
         )
         
def referer_redirect(user, request):
  '''Redirect a user to where he came from. If he didn't come from anywhere,
    refer him to a default location.'''
  if 'HTTP_REFERER' in request.META:
    return HttpResponseRedirect(request.META['HTTP_REFERER'])
  return default_list_redirect(user)