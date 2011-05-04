# coding=utf-8

from base_request_handler import BaseRequestHandler

import urllib

from google.appengine.ext.webapp import template
template.register_template_library('dnzo_templating')

TEMPLATES_DIR = 'resources/templates/'

COOKIE_STATUS = 'dnzo-status'
COOKIE_UNDO   = 'dnzo-undo'

def dnzo_login_required(fn):
  """Decorator for a BaseAPIRequestHelper to make it require a DNZO login."""
  def logged_in_wrapper(self, *args, **kwargs):
    if not self.dnzo_user:
      self.login_required()
    else:
      fn(self, *args, **kwargs)
  return logged_in_wrapper
  
class NotFoundHandler(BaseRequestHandler):
  def __init__(self):
    super(NotFoundHandler, self).__init__(TEMPLATES_DIR)
  def get(self):
    self.not_found()
  def post(self):
    self.not_found()

class DNZORequestHandler(BaseRequestHandler):
  def __init__(self):
    super(DNZORequestHandler, self).__init__(TEMPLATES_DIR)
    
    from tasks_data.users import get_dnzo_user
    self.dnzo_user = get_dnzo_user()
    
  def always_includes(self, is_handling_error):
    return {
      'user': self.dnzo_user,
    }
    
  def default_list_redirect(self):
    '''Redirect a user to his defalt task list.'''
    from tasks_data.task_lists import get_task_lists
    
    lists = get_task_lists(self.dnzo_user)
    if lists and len(lists) > 0:
      self.list_redirect(lists[0])
    else:
      from google.appengine.api.users import create_logout_url
      import logging
      logging.error("Somehow this user does not have any task lists! Logging the user out.")
      self.redirect(create_logout_url('/'))

  def list_redirect(self, task_list):
    self.redirect('/l/%s/' % urllib.quote(task_list.short_name))
  
  def referer_redirect(self):
    super(DNZORequestHandler,self).referer_redirect(self.most_recent_redirect)
  
  def most_recent_redirect(self):     
    if self.dnzo_user.most_recent_uri:
      self.redirect(self.dnzo_user.most_recent_uri)
    else:
      self.default_list_redirect()
  
  #
  # STATUSING
  #
  def get_status_undo(self):
    import Cookie
    from tasks.statusing import get_status_message
    
    status = None
    
    cookie = Cookie.SimpleCookie(self.request.headers.get('Cookie'))
    if COOKIE_STATUS in cookie:
      status = cookie[COOKIE_STATUS].value
      
    try:
      undo = int(cookie[COOKIE_UNDO].value)
    except:
      undo = None
      
    self.reset_status_undo(status, undo)
    return (get_status_message(status), undo)

  def reset_status_undo(self, status=None, undo=None):
    if status is not None:
      self.set_cookie(COOKIE_STATUS, '', max_age=-1)
    if undo is not None:
      self.set_cookie(COOKIE_UNDO, '', max_age=-1)
  
  def set_status_undo(self, status=None, undo=None):
    if status is not None:
      self.set_cookie(COOKIE_STATUS, status, max_age=60)
    if undo is not None:
      self.set_cookie(COOKIE_UNDO, str(undo.key().id()), max_age=60)
