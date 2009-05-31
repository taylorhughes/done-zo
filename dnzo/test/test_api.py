import unittest
from os import path

from webtest import TestApp
from google.appengine.ext import webapp
from django.utils import simplejson as json

from api.main import API_URLS, API_PREFIX
from test.fixtures import setup_fixtures

from tasks_data.models import Task

BOGUS_IDS = ('abc', '-1', '0.1234', '1.', '.1', ' 123 ', '99999')

class TaskAPITest(unittest.TestCase):
  def setUp(self):
    setup_fixtures()
    self.application = webapp.WSGIApplication(API_URLS, debug=True)

  def test_get_task(self):
    app = TestApp(self.application)

    all_tasks_response = app.get(path.join(API_PREFIX,'t'))
    self.assertEqual('200 OK', all_tasks_response.status)

    for task in Task.all():
      task_id = str(task.key().id())
      response = app.get(path.join(API_PREFIX,'t',task_id))
      self.assertEqual('200 OK', response.status)
      self.assertTrue(json.dumps(task.body) in response,
                      "Response should include JSON-encoded task body.")
      self.assertTrue(json.dumps(task.project) in response,
                      "Response should include task's project.")

      self.assertTrue(json.dumps(task.body) in all_tasks_response,
                      "/t/ response should include all tasks' bodies.")
      self.assertTrue(json.dumps(task.project) in all_tasks_response,
                      "/t/ response should include all tasks' projects.")

    for bogus_id in BOGUS_IDS:
      response = app.get(path.join(API_PREFIX,'t',bogus_id), expect_errors=True)
      self.assertTrue('404 Not Found' in response.status,
                      "Bogus ID task should be Not Found, but response was (%s)" % response.status)