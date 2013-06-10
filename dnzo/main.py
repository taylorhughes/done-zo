
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import environment
from urls import ALL_URLS

def main():
  os.environ['DJANGO_SETTINGS_MODULE'] = 'django_settings'
  routes = [webapp.Route(path, handler=handler, name=handler.__name__) for path, handler in ALL_URLS]
  application = webapp.WSGIApplication(routes, debug=environment.IS_DEVELOPMENT)
  application.error_handlers[404] = handle_404
  run_wsgi_app(application)

def handle_404(request, response, exception):
  from dnzo_request_handler import NotFoundHandler
  handler = NotFoundHandler(request, response)

  slashed_url = request.url + '/'
  slashed_request = webapp.Request.blank(slashed_url)
  try:
    matches = request.app.router.match(slashed_request)
  except webapp.exc.HTTPNotFound:
    matches = None

  if matches:
    handler.redirect(slashed_url)
  else:
    handler.get()

if __name__ == '__main__':
  main()