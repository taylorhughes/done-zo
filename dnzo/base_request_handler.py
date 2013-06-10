import logging
from os import path

import webapp2
from django.template import loader as template_loader
from django.template import Context


AJAX_HEADER   = 'X-Requested-With'
REFERER_HEADER = 'Referer'


class BaseRequestHandler(webapp2.RequestHandler):
  def __init__(self, *args):
    super(BaseRequestHandler, self).__init__(*args)
    self.__cookie_set = None
    self.__is_handling_error = False

  def login_required(self):
    self.access_error_redirect()
    
  def not_found(self):
    self.error(404)
    self.render('404.html')
    
  def is_handling_error(self):
    return self.__is_handling_error

  def handle_exception(self, exception, debug_mode):
    if debug_mode:
      super(BaseRequestHandler,self).handle_exception(exception,debug_mode)
    else:
      logging.exception("An exception occurred. Rendered a 500 error message. Yikes!")
      self.__is_handling_error = True
      self.error(500)
      self.render('500.html')

  def is_ajax(self):
    if AJAX_HEADER in self.request.headers and self.request.headers[AJAX_HEADER] == 'XMLHttpRequest':
      return True
    return False
  
  #
  #  TEMPLATING
  #
  def render(self, template_name, **kwargs):
    template_values = self.always_includes(self.is_handling_error())
    template_values.update(kwargs)
    
    template = template_loader.get_template(template_name)
    response = template.render(Context(template_values))

    self.render_text(response)

  def render_text(self, text):
    self.response.out.write(text)

  def always_includes(self, is_handling_error):
    return {}

  #
  # REDIRECTS
  #
  def url_for(self, handler_name, *args):
    app = webapp2.WSGIApplication.active_instance
    return app.router.build(self.request, handler_name, args, {})

  def redirect_to(self,*args):
    self.redirect(self.url_for(*args))
    
  def access_error_redirect(self):
    # TODO: Redirect to some kind of 5xx access denied error.
    import logging
    logging.error("Access error; redirecting to /.")
    self.redirect('/')
    
  def referer_uri(self):
    if REFERER_HEADER in self.request.headers:
      return self.request.headers[REFERER_HEADER]
    return None
    
  def referer_redirect(self, default_callback=None):
    '''Redirect a user to where he came from. If he didn't come from anywhere,
      refer him to a default location.'''
    referer = self.referer_uri()
    if referer:
      self.redirect(referer)
    elif default_callback:
      default_callback()
    
  def set_cookie(self, key, value, max_age=None, path="/"):
    import Cookie
    
    if not self.__cookie_set:
      self.__cookie_set = Cookie.SimpleCookie()
    
    self.__cookie_set[key] = value
    if max_age:
      self.__cookie_set[key]['Max-Age'] = max_age
    if path:
      self.__cookie_set[key]['Path'] = path
      
    for cookie in self.__cookie_set.output(header='').split('\n'):
      self.response.headers.add_header('Set-Cookie', cookie)
