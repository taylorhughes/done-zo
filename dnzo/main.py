from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import environment
from urls import ALL_URLS

def main():
  application = webapp.WSGIApplication(ALL_URLS, debug=environment.IS_DEVELOPMENT)
  run_wsgi_app(application)

if __name__ == '__main__':
  main()