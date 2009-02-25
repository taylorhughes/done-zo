
from django.http import HttpResponseRedirect

def access_error_redirect():
  # TODO: Redirect to some kind of 5xx access denied error.
  import logging
  logging.error("Access error; redirecting to /.")
  return HttpResponseRedirect('/')

def default_list_redirect(user):
  '''Redirect a user to his defalt task list.'''
  from tasks_data.task_lists import get_task_lists
  
  lists = get_task_lists(user)
  if lists and len(lists) > 0:
    return list_redirect(user, lists[0])
  else:
    import logging
    # TODO: Log user out.
    logging.error("Somehow this user does not have any task lists.")
    return HttpResponseRedirect('/')

def list_redirect(user, list):
  from django.core.urlresolvers import reverse as reverse_url
  return HttpResponseRedirect(
           reverse_url('tasks.views.list_index',
                       args=[list.short_name]
           )
         )
         
def referer_redirect(user, request):
  '''Redirect a user to where he came from. If he didn't come from anywhere,
    refer him to a default location.'''
  from util.misc import get_referer
  referer = get_referer(request)
  if referer is not None:
    return HttpResponseRedirect(referer)
  return most_recent_redirect(user)

def most_recent_redirect(user):
  if user.most_recent_uri:
    return HttpResponseRedirect(user.most_recent_uri)
  return default_list_redirect(user)