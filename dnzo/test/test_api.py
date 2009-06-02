import unittest
import os
from os import path
import logging

from webtest import TestApp

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.tools.dev_appserver_login import COOKIE_NAME, CreateCookieData

from django.utils import simplejson as json

from api.main import API_URLS, API_PREFIX
from test.fixtures import setup_fixtures, DUMMY_USER_ADDRESS, ANOTHER_USER_ADDRESS

from tasks_data.models import Task, TasksUser


BOGUS_IDS = ('abc', '-1', '0.1234', '1.', '.1', ' 123 ', '99999')

class TaskAPITest(unittest.TestCase):
  def setUp(self):
    setup_fixtures()
    self.application = webapp.WSGIApplication(API_URLS, debug=True)
    self.app = TestApp(self.application)
    self.dnzo_user = TasksUser.gql('WHERE user=:1', users.User(DUMMY_USER_ADDRESS)).get()
    
    # make it look like the request is coming from this user
    os.environ['USER_EMAIL'] = self.dnzo_user.email
    
  def test_get_task(self):
    all_tasks_response = self.app.get(path.join(API_PREFIX,'t'))
    self.assertEqual('200 OK', all_tasks_response.status)

    tasks = Task.gql('where ancestor is :user',user=self.dnzo_user).fetch(1000)
    self.assertTrue(len(tasks) > 0, "There should be some tasks from the user.")
    for task in tasks:
      task_id = str(task.key().id())
      response = self.app.get(path.join(API_PREFIX,'t',task_id))
      self.assertEqual('200 OK', response.status)
      self.assertTrue(json.dumps(task.body) in response,
                      "Response should include JSON-encoded task body.")
      self.assertTrue(json.dumps(task.project) in response,
                      "Response should include task's project.")

      self.assertTrue(json.dumps(task.body) in all_tasks_response,
                      "/t/ response should include all tasks' bodies.")
      self.assertTrue(json.dumps(task.project) in all_tasks_response,
                      "/t/ response should include all tasks' projects.")
                      
    another_user = TasksUser.gql('WHERE user=:1', users.User(ANOTHER_USER_ADDRESS)).get()
    tasks = Task.gql('where ancestor is :user',user=another_user).fetch(1000)
    self.assertTrue(len(tasks) > 0, "There should be some tasks from another user.")
    for task in tasks:
      task_id = str(task.key().id())
      response = self.app.get(path.join(API_PREFIX,'t',task_id), expect_errors=True)
      self.assertEqual('404 Not Found', response.status)

    for bogus_id in BOGUS_IDS:
      response = self.app.get(path.join(API_PREFIX,'t',bogus_id), expect_errors=True)
      self.assertTrue('404 Not Found' in response.status,
                      "Bogus ID task should be Not Found, but response was (%s)" % response.status)