# coding=utf-8

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from os import path
import logging
        
TEMPLATES_DIR = 'resources/templates/'

COOKIE_STATUS = 'dnzo-status'
COOKIE_UNDO   = 'dnzo-undo'

webapp.template.register_template_library('templating')

def dnzo_login_required(fn):
  """Decorator for a BaseAPIRequestHelper to make it require a DNZO login."""
  def logged_in_wrapper(self, *args):
    if not self.dnzo_user:
      self.login_required()
    else:
      fn(self, *args)
  return logged_in_wrapper
  
class DNZORequestHandler(webapp.RequestHandler):
  def __init__(self):
    from tasks_data.users import get_dnzo_user
    self.dnzo_user = get_dnzo_user()
    
    self.__cookie_set = None
    
  def login_required(self):
    self.access_error_redirect()
    
  def not_found(self):
    self.error(404)
    self.render('404.html')

  def is_ajax(self):
    for header in ['HTTP_X_REQUESTED_WITH', 'X-Requested-With']:
      if header in self.request.headers and self.request.headers[header] == 'XMLHttpRequest':
        return True
    return False
  
  #
  #  TEMPLATING
  #
  def render(self, template_name, **kwargs):
    template_path = path.join(path.dirname(__file__), TEMPLATES_DIR, template_name)
    template_values = self.always_includes()
    template_values.update(kwargs)

    import django.conf
    setattr(django.conf.settings, 'DEFAULT_CONTENT_TYPE', 'text/html;charset=UTF-8')
    
    response = template.render(template_path, template_values, True)

    self.response.out.write(response)

  def always_includes(self):
    return {
      'user': self.dnzo_user,
    }

  #
  # REDIRECTS
  #
  def access_error_redirect(self):
    # TODO: Redirect to some kind of 5xx access denied error.
    logging.error("Access error; redirecting to /.")
    self.redirect('/')

  def default_list_redirect(self):
    '''Redirect a user to his defalt task list.'''
    from tasks_data.task_lists import get_task_lists
    
    lists = get_task_lists(self.dnzo_user)
    if lists and len(lists) > 0:
      self.list_redirect(lists[0])
    else:
      import logging
      # TODO: Log user out.
      logging.error("Somehow this user does not have any task lists!")
      return self.redirect('/')

  def list_redirect(self, task_list):
    from urls import list_url
    self.redirect(list_url(task_list))
    
  def referer_redirect(self):
    '''Redirect a user to where he came from. If he didn't come from anywhere,
      refer him to a default location.'''
    if 'HTTP_REFERER' in self.request.headers:
      referer = self.request.headers['HTTP_REFERER']
      self.redirect(referer)
    else:
      self.most_recent_redirect()

  def most_recent_redirect(self):      
    if self.dnzo_user.most_recent_uri:
      self.redirect(self.dnzo_user.most_recent_uri)
    else:
      self.default_list_redirect()
    
  def set_cookie(self, key, value, max_age=None, path="/"):
    import Cookie
    
    if not self.__cookie_set:
      self.__cookie_set = Cookie.SimpleCookie()
    
    self.__cookie_set[key] = value
    if max_age:
      self.__cookie_set[key]['Max-Age'] = max_age
    if path:
      self.__cookie_set[key]['Path'] = path
      
    self.response.headers['Set-Cookie'] = self.__cookie_set.output(header='')
    
  #
  # STATUSING
  #
  def get_status_undo(self):
    import Cookie
    from tasks.statusing import get_status_message
    from util.misc       import param
    
    status = None
    
    cookie = Cookie.SimpleCookie(self.request.headers.get('Cookie'))
    if COOKIE_STATUS in cookie:
      status = cookie[COOKIE_STATUS].value
      
    try:
      from util.misc import param
      undo = int(param(COOKIE_UNDO, cookie, None))
    except:
      undo = None
      
    self.reset_status_undo(status,undo)
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
