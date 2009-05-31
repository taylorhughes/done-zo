import unittest
from os import path

from webtest import TestApp
from google.appengine.ext import webapp
from django.utils import simplejson as json

from api.main import API_URLS, API_PREFIX
from test.fixtures import setup_fixtures

from tasks_data.models import Task

class TaskAPITest(unittest.TestCase):
  def setUp(self):
    setup_fixtures()
    self.application = webapp.WSGIApplication(API_URLS, debug=True)

  def test_task(self):
    app = TestApp(self.application)

    for task in Task.all():
      task_id = str(task.key().id())
      response = app.get(path.join(API_PREFIX,'t',task_id))
      self.assertEqual('200 OK', response.status)
      self.assertTrue(json.dumps(task.body) in response,
                      "Response should include JSON-encoded task body.")