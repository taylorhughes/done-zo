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

from tasks_data.models import Task, TasksUser, TaskList
from tasks_data.tasks import DEFAULT_TASKS

from copy import deepcopy

from datetime import datetime

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
    
  def test_updated_since(self):
    tasks = Task.gql('where ancestor is :user',user=self.dnzo_user).fetch(1000)
    self.assertTrue(len(tasks) > 0, "There should be some tasks from the user.")
    
    now = datetime.utcnow()
    
    response = self.app.get(TASK_PATH, params={ 'updated_since': now })
    task_dicts = json.loads(response.body)['tasks']
    self.assertEqual(0, len(task_dicts), "There should be no tasks updated since now.")
    
    old_now = now
    
    for task in tasks:
      task_id = str(task.key().id())
      
      changes = { 'body': task.body + "!!!!!!!" }
      response = self.app.put(path.join(TASK_PATH, task_id), params=changes)
      self.assertEqual('200 OK', response.status)
      
      response = self.app.get(TASK_PATH, params={ 'updated_since': now })
      task_dicts = json.loads(response.body)['tasks']
      self.assertEqual(1, len(task_dicts), "There should be ONE task updated since now, the one we just changed.")
      
      now = datetime.utcnow()
      
    response = self.app.get(TASK_PATH, params={ 'updated_since': old_now })
    task_dicts = json.loads(response.body)['tasks']
    self.assertEqual(len(tasks), len(task_dicts), "The list of updated tasks should be the same as the number of tasks since we just cahnged all of them.")
    
    
  def test_post_task(self):
    task_list = TaskList.gql('where ancestor is :user', user=self.dnzo_user).get()
    for task_data in DEFAULT_TASKS:
      task_data = deepcopy(task_data)
      
      response = self.app.post(TASK_PATH, params=task_data, expect_errors=True)
      self.assertTrue('task_list' not in task_data, "Should not be submitting a task list, wtf?")
      self.assertEqual('400 Bad Request', response.status, "Response should be 400 because no task list was provided, but was %s." % response.status)
      
      task_data['task_list'] = 'not-a-list'
      response = self.app.post(TASK_PATH, params=task_data, expect_errors=True)
      self.assertEqual('400 Bad Request', response.status, "Response should be 400 because a fake list was provided.")
      
      task_data['task_list'] = task_list.short_name
      response = self.app.post(TASK_PATH, params=task_data)
      self.assertEqual('200 OK', response.status)
      
      dictresponse = json.loads(response.body)['task']
      self.assertTrue('id' in dictresponse, "Response should contain a JS dict with an ID of the new task")
      
      response = self.app.get(path.join(TASK_PATH, str(dictresponse['id'])))
      dictresponse = json.loads(response.body)['task']
      self.assertEqual('200 OK', response.status, "Should be able to GET /t/id")
      
      self.assertEqual(task_data['body'], dictresponse['body'], "Body should be equal to what we posted!")
      
  def test_put_task(self):
    tasks = Task.gql('where ancestor is :user',user=self.dnzo_user).fetch(1000)
    self.assertTrue(len(tasks) > 0, "There should be some tasks from the user.")
    for task in tasks:
      task_id = str(task.key().id())
      
      new_project = "New Project"
      appendage = "here's something added to the task body!"
      changes = { 'body': task.body + appendage, 'project': new_project }
      response = self.app.put(path.join(TASK_PATH, task_id), params=changes)
      self.assertEqual('200 OK', response.status)
      
      response = self.app.get(path.join(TASK_PATH,task_id))
      self.assertEqual('200 OK', response.status)
      task_dict = json.loads(response.body)['task']
      self.assertEqual(changes['body'], task_dict['body'], "New body should reflect changes, but was %s!" % repr(task_dict['body']))
      self.assertEqual(changes['project'], task_dict['project'], "New project should reflect changes!")
      
    another_user = TasksUser.gql('WHERE user=:1', users.User(ANOTHER_USER_ADDRESS)).get()
    tasks = Task.gql('where ancestor is :user',user=another_user).fetch(1000)
    self.assertTrue(len(tasks) > 0, "There should be some tasks from another user.")
    for task in tasks:
      appendage = "here's something added to the task body!"
      changes = { 'body': task.body + appendage }
      task_id = str(task.key().id())
      response = self.app.put(path.join(API_PREFIX,'t',task_id), expect_errors=True, params=changes)
      self.assertEqual('404 Not Found', response.status, "Should not allow PUT against another person's tasks")
      
      
  def test_delete_task(self):
    tasks = Task.gql('where ancestor is :user',user=self.dnzo_user).fetch(1000)
    self.assertTrue(len(tasks) > 0, "There should be some tasks from the user.")
    for task in tasks:
      task_id = str(task.key().id())
      
      response = self.app.get(path.join(TASK_PATH,task_id), expect_errors=True)
      self.assertEqual('200 OK', response.status)
      
      response = self.app.delete(path.join(TASK_PATH, task_id))
      self.assertEqual('200 OK', response.status)
      
      response = self.app.get(path.join(TASK_PATH,task_id), expect_errors=True)
      self.assertEqual('404 Not Found', response.status, "Task should be deleted!")
      response = self.app.delete(path.join(TASK_PATH, task_id), expect_errors=True)
      self.assertEqual('404 Not Found', response.status, "Task should be deleted!")
      
    another_user = TasksUser.gql('WHERE user=:1', users.User(ANOTHER_USER_ADDRESS)).get()
    tasks = Task.gql('where ancestor is :user',user=another_user).fetch(1000)
    self.assertTrue(len(tasks) > 0, "There should be some tasks from another user.")
    for task in tasks:
      task_id = str(task.key().id())
      
      response = self.app.delete(path.join(API_PREFIX,'t',task_id), expect_errors=True)
      self.assertEqual('404 Not Found', response.status, "Should not allow DELETE against another person's tasks")
      
      
  def test_get_task(self):
    all_tasks_response = self.app.get(TASK_PATH)
    
    all_tasks_raw = json.loads(all_tasks_response.body)
    all_tasks = {}
    self.assertTrue('tasks' in all_tasks_raw, "Tasks GET should return a dictionary with 'tasks' in it")
    self.assertTrue('error' not in all_tasks_raw, "Tasks GET should not include an error.")
    for task in all_tasks_raw['tasks']:
      all_tasks[str(task['id'])] = task
    
    self.assertEqual(0, len(filter(lambda t: t['archived'], all_tasks_raw['tasks'])), "All tasks shown should be not archived.")
    
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
                      
                      
                      
                      
                      