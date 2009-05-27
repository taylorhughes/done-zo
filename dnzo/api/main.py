
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from api.views import TasksHandler, TaskHandler

import environment

API_PREFIX = '/api/0.1/'
API_URLS = [
  (API_PREFIX + r't/(?P<task_id>[0-9]+)/?', TaskHandler),
  (API_PREFIX + r't/?', TasksHandler),
]

def main():
  application = webapp.WSGIApplication(API_URLS, debug=environment.IS_DEVELOPMENT)
  run_wsgi_app(application)

if __name__ == '__main__':
  main()