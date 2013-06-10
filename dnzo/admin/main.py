import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import environment
from admin.urls import ADMIN_URLS

def main():
  os.environ['DJANGO_SETTINGS_MODULE'] = 'django_settings'
  routes = [webapp.Route(path, handler=handler, name=handler.__name__) for path, handler in ADMIN_URLS]
  application = webapp.WSGIApplication(routes, debug=environment.IS_DEVELOPMENT)
  run_wsgi_app(application)

if __name__ == '__main__':
  main()