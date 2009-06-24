import unittest
import os
from os import path
import logging

from webtest import TestApp

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.tools.dev_appserver_login import COOKIE_NAME, CreateCookieData

from django.utils import simplejson as json

from urls import API_URLS, API_PREFIX
from test.fixtures import setup_fixtures, DUMMY_USER_ADDRESS, ANOTHER_USER_ADDRESS

from tasks_data.models import Task, TasksUser
from tasks_data.tasks import DEFAULT_TASKS

BOGUS_IDS = ('abc', '-1', '0.1234', '1.', '.1', ' 123 ', '99999')
TASK_PATH = path.join(API_PREFIX,'t')

class TaskAPITest(unittest.TestCase):
  def setUp(self):
    setup_fixtures()
    self.application = webapp.WSGIApplication(API_URLS, debug=True)
    self.app = TestApp(self.application)
    self.dnzo_user = TasksUser.gql('WHERE user=:1', users.User(DUMMY_USER_ADDRESS)).get()
    
    # make it look like the request is coming from this user
    os.environ['USER_EMAIL'] = self.dnzo_user.email
    
  def test_post_task(self):
    for task_data in DEFAULT_TASKS:
      response = self.app.post(TASK_PATH, params=task_data)
      self.assertEqual('200 OK', response.status)
      
      dictresponse = json.loads(response.body)['task']
      self.assertTrue('id' in dictresponse, "Response should contain a JS dict with an ID of the new task")
      
      response = self.app.get(path.join(TASK_PATH, str(dictresponse['id'])))
      dictresponse = json.loads(response.body)['task']
      self.assertEqual('200 OK', response.status, "Should be able to GET /t/id")
      
      self.assertEqual(task_data['body'], dictresponse['body'], "Body should be equal to what we posted!")
      
  def test_get_task(self):
    all_tasks_response = self.app.get(TASK_PATH)
    
    all_tasks_raw = json.loads(all_tasks_response.body)
    all_tasks = {}
    self.assertTrue('tasks' in all_tasks_raw, "Tasks GET should return a dictionary with 'tasks' in it")
    self.assertTrue('error' not in all_tasks_raw, "Tasks GET should not include an error.")
    for task in all_tasks_raw['tasks']:
      all_tasks[str(task['id'])] = task
    
    self.assertEqual('200 OK', all_tasks_response.status)

    tasks = Task.gql('where ancestor is :user',user=self.dnzo_user).fetch(1000)
    self.assertTrue(len(tasks) > 0, "There should be some tasks from the user.")
    for task in tasks:
      task_id = str(task.key().id())
      self.assertTrue(task_id in all_tasks, "Task ID should appear in the list of all tasks from before")
      
      response = self.app.get(path.join(TASK_PATH,task_id))
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
      self.assertTrue(task_id not in all_tasks, "Task ID from another user should NOT appear in the list of all tasks from before")

    for bogus_id in BOGUS_IDS:
      response = self.app.get(path.join(API_PREFIX,'t',bogus_id), expect_errors=True)
      self.assertTrue('404 Not Found' in response.status,
                      "Bogus ID task should be Not Found, but response was (%s)" % response.status)
                      
                      
                      
                      
                      