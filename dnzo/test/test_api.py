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

from util.human_time import parse_datetime

from tasks_data.models import Task, TasksUser, TaskList
from tasks_data.tasks import DEFAULT_TASKS, get_tasks

import random
from copy import deepcopy

from datetime import datetime, timedelta

BOGUS_IDS = ('abc', '-1', '0.1234', '1.', '.1', ' 123 ', '99999', ' a b c 1 2 ')
TASK_PATH = path.join(API_PREFIX,'t/')
LIST_PATH = path.join(API_PREFIX,'l/')
LIST_PATH_FMT = path.join(API_PREFIX,'l/%s/')
ARCHIVED_PATH = path.join(API_PREFIX,'a/')

class TaskAPITest(unittest.TestCase):
  def setUp(self):
    setup_fixtures()
    self.application = webapp.WSGIApplication(API_URLS, debug=True)
    self.app = TestApp(self.application)
    self.dnzo_user = TasksUser.gql('WHERE user=:1', users.User(DUMMY_USER_ADDRESS)).get()
    
    # make it look like the request is coming from this user
    os.environ['USER_EMAIL'] = self.dnzo_user.email
  
  def test_get_task_lists(self):
    task_list = TaskList.gql('where ancestor is :user', user=self.dnzo_user).get()

    response = self.app.get(LIST_PATH)
    self.assertTrue('200 OK' in response.status)
    
    self.assertTrue(json.dumps(task_list.name) in response.body, "Task list name should appear in response body")
    
    task_lists = json.loads(response.body)['task_lists']
    self.assertEquals(task_list.name, task_lists[0]['name'], "Task list name should be the same!")

    self.assertEqual(1, len(task_lists), "There should only be one task list!")
    
    tasks = get_tasks(self.dnzo_user, task_list=task_list)
    self.assertEqual(len(tasks), task_lists[0]['tasks_count'], "Tasks count is not accurate!")
    
  def test_post_task_lists(self):
    task_list_name = "Another task list"
    from util.misc import slugify
    slug = slugify(task_list_name)
    
    response = self.app.post(LIST_PATH, expect_errors=True)
    self.assertTrue("400 Bad Request" in response.status, "Response should be bad because we didn't supply a task list name")
    
    response = self.app.post(LIST_PATH, params={ 'task_list_name': task_list_name })
    self.assertTrue(json.dumps(slug) in response, "Slug should appear in new task as the key")
    
    new_task_list = json.loads(response.body)['task_list']
    self.assertEqual(task_list_name, new_task_list['name'], "New task list name should be the one we provided!")
    self.assertEqual(slug, new_task_list['key'], "Key for the new list should be the slug we created")
    
    response = self.app.get(LIST_PATH)
    task_list_dicts = json.loads(response.body)['task_lists']
    task_lists = TaskList.gql('where ancestor is :user', user=self.dnzo_user).fetch(100)

    self.assertEqual(len(task_lists), len(task_list_dicts), "Response did not contain all of our task lists apparently")

  def test_get_task_list(self):
    task_list = TaskList.gql('where ancestor is :user', user=self.dnzo_user).get()
    response = self.app.get(LIST_PATH_FMT % str(task_list.short_name))
    self.assertTrue(json.dumps(task_list.name) in response.body, "Response should contain new task name")
    
    task_list_dict = json.loads(response.body)['task_list']
    self.assertEqual(task_list.name, task_list_dict['name'])
    self.assertEqual(task_list.short_name, task_list_dict['key'])
    self.assertEqual(task_list.deleted, task_list_dict['deleted'])
    
  def test_delete_task_list(self):
    task_list = TaskList.gql('where ancestor is :user', user=self.dnzo_user).get()
    response = self.app.get(LIST_PATH_FMT % str(task_list.short_name))
    task_list_dict = json.loads(response.body)['task_list']

    self.assertTrue(not task_list_dict['deleted'], "Task list should not be deleted.")
    
    response = self.app.delete(LIST_PATH_FMT % str(task_list.short_name), expect_errors=True)
    
    self.assertTrue('400 Bad Request' in response.status, "Status should be 400 because we're deleting the only list")

    response = self.app.get(LIST_PATH_FMT % str(task_list.short_name))
    task_list_dict = json.loads(response.body)['task_list']
    self.assertTrue(not task_list_dict['deleted'], "Task list should NOT be deleted!")

    # ADD A NEW TASK LIST, now we can delete the first one.
    self.app.post(LIST_PATH, params={ 'task_list_name': "Another task list!" })
    
    response = self.app.delete(LIST_PATH_FMT % str(task_list.short_name))
    task_list_dict = json.loads(response.body)['task_list']
    self.assertTrue(task_list_dict['deleted'], "Task list should be deleted now.")
    
    response = self.app.get(LIST_PATH)
    self.assertTrue(not json.dumps(task_list.short_name) in response.body, "Deleted task list should NOT be in this list!")

  def test_max_num_tasks(self):
    from tasks_data.tasks import MAX_ACTIVE_TASKS
    
    response = self.app.post(LIST_PATH, params={ 'task_list_name': 'Some new list' })
    self.assertEqual('200 OK', response.status)
    task_list = json.loads(response.body)['task_list']
    
    tasks = []
    
    for task_data in [DEFAULT_TASKS[i % (len(DEFAULT_TASKS) - 1)] for i in range(0,MAX_ACTIVE_TASKS)]:
      task_data = deepcopy(task_data)
      task_data['task_list'] = task_list['key']
            
      response = self.app.post(TASK_PATH, params=task_data)
      self.assertEqual('200 OK', response.status)
      
      tasks.append(json.loads(response.body)['task'])
      
    response = self.app.get(LIST_PATH_FMT % str(task_list['key']))
    self.assertEqual('200 OK', response.status)
    task_list = json.loads(response.body)['task_list']
    
    self.assertEqual(MAX_ACTIVE_TASKS, task_list['tasks_count'])
    
    task_data = deepcopy(DEFAULT_TASKS[0])
    task_data['task_list'] = task_list['key']
    response = self.app.post(TASK_PATH, params=task_data, expect_errors=True)
    self.assertEqual('400 Bad Request', response.status, "Response should be 400 because we added one more than the max number of tasks; was %s." % response.status)
    # Twice for good measure
    response = self.app.post(TASK_PATH, params=task_data, expect_errors=True)
    self.assertEqual('400 Bad Request', response.status, "Response should be 400 because we added one more than the max number of tasks.")

    # Delete a task, then add one successfully
    last_task = tasks.pop()
    response = self.app.delete('%s%s/' % (TASK_PATH, last_task['id']))
    self.assertEqual('200 OK', response.status, "Should be able to delete a task.")
    
    response = self.app.post(TASK_PATH, params=task_data)
    self.assertEqual('200 OK', response.status, "Should be able to post a new task because the last one was deleted.")
    
    response = self.app.post(TASK_PATH, params=task_data, expect_errors=True)
    self.assertEqual('400 Bad Request', response.status, "Response should be 400 because we added one more than the max number of tasks.")
    
    # Archive a task
    last_task = tasks.pop()
    response = self.app.put('%s%s/' % (TASK_PATH, last_task['id']), params={ 'complete': 'true', 'archived': 'true' })
    self.assertEqual('200 OK', response.status, "Should be able to archive a task.")
    archived_task = json.loads(response.body)['task']
    
    response = self.app.get(TASK_PATH, params={ 'task_list': str(task_list['key']) })
    current_tasks = json.loads(response.body)['tasks']
    self.assertEqual(MAX_ACTIVE_TASKS - 1, len(current_tasks), "Task was not archived, task list contents is incorrect")
    
    response = self.app.get(LIST_PATH_FMT % str(task_list['key']))
    current_list = json.loads(response.body)['task_list']
    self.assertEqual(MAX_ACTIVE_TASKS - 1, current_list['tasks_count'], "Task count was wrong (got %s)" % (current_list['tasks_count']))
    
    response = self.app.post(TASK_PATH, params=task_data)
    self.assertEqual('200 OK', response.status, "Should be able to post a new task because the last one was archived.")

    # Delete an ARCHIVED TASK. This should not lower the active tasks count, so this should be an error.
    self.assertEqual(archived_task['archived'], True)
    response = self.app.delete('%s%s/' % (TASK_PATH, archived_task['id']))
    self.assertEqual('200 OK', response.status)
    
    # This should STILL BE 400 even though we just deleted a task, because that task should be archived.
    response = self.app.post(TASK_PATH, params=task_data, expect_errors=True)
    self.assertEqual('400 Bad Request', response.status, "Response should be 400 because we added one more than the max number of tasks.")

    task_data['complete'] = 'true'
    task_data['archived'] = 'true'
    response = self.app.post(TASK_PATH, params=task_data)
    self.assertEqual('200 OK', response.status, "Should be able to post a new ARCHIVED task.")
    
    new_archived_task = json.loads(response.body)['task']
    response = self.app.put('%s%s/' % (TASK_PATH, new_archived_task['id']), params={ 'archived': 'false' }, expect_errors=True)
    self.assertEqual('400 Bad Request', response.status, "Response should be 400 because we are attempting to unarchive a task when we have no room, was %s." % response.status)
    
    # Archive a task
    last_task = tasks.pop()
    response = self.app.put('%s%s/' % (TASK_PATH, str(last_task['id'])), params={ 'complete': 'true', 'archived': 'true' })
    self.assertEqual('200 OK', response.status, "Should be able to archive a task.")
    
    response = self.app.put('%s%s/' % (TASK_PATH, str(new_archived_task['id'])), params={ 'archived': 'false' })
    self.assertEqual('200 OK', response.status, "Response should be OK now, was %s." % response.status)
    

  def test_post_task(self):
    task_list = TaskList.gql('where ancestor is :user', user=self.dnzo_user).get()
    i = 0
    for task_data in DEFAULT_TASKS:
      task_data = deepcopy(task_data)
      if i % 2 == 0:
        task_data['complete'] = 'true'
        now = datetime.utcnow()
        task_data['sort_date'] = str(now + timedelta(microseconds=int(random.random()*100000)))
        self.assertTrue(now != task_data['sort_date'], "Sort date should not be the same as utcnow.")
      i += 1
      
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
      self.assertTrue('updated_at' in dictresponse, "Response should include the updated_at timestamp")
      self.assertTrue('sort_date' in dictresponse, "Response should include the sort_date timestamp")
      self.assertTrue('complete' in dictresponse, "Response should include whether the task is complete")
      self.assertTrue('task_list_name' not in dictresponse, "Non-archived tasks should not include the task list name")
      self.assertEqual(dictresponse['complete'], 'archived' in dictresponse, "Archived should only appear in task body if the task is complete")
      
      if 'complete' in task_data and task_data['complete'] == 'true':
        self.assertEqual(dictresponse['complete'], True)
      else:
        self.assertEqual(dictresponse['complete'], False)
        
      self.assertTrue(dictresponse['updated_at'] is not None, "Updated_at timestamp should not be none")
      initial_updated_at = dictresponse['updated_at']
      
      response = self.app.get('%s%s/' % (TASK_PATH, str(dictresponse['id'])))
      dictresponse = json.loads(response.body)['task']
      self.assertEqual('200 OK', response.status, "Should be able to GET /t/id")
      
      self.assertEqual(task_data['body'], dictresponse['body'], "Body should be equal to what we posted!")
      self.assertEqual(initial_updated_at, dictresponse['updated_at'], "Updated at should not change between saving and reloading, but was %s and %s" % (str(initial_updated_at), str(dictresponse['updated_at'])))
      if 'sort_date' in task_data:
        logging.info(">>> Sort dates are (%s) and (%s)", task_data['sort_date'], dictresponse['sort_date'])
        self.assertEqual(task_data['sort_date'], dictresponse['sort_date'], "Sort date was not properly saved on insert, was %s and %s" % (task_data['sort_date'], dictresponse['sort_date']))
        
      
  def test_put_task(self):
    tasks = Task.gql('where ancestor is :user',user=self.dnzo_user).fetch(1000)
    self.assertTrue(len(tasks) > 0, "There should be some tasks from the user.")
    for task in tasks:
      task_id = str(task.key().id())
      
      old_updated_at = str(task.updated_at)
      new_project = "New Project"
      appendage = "here's something added to the task body!"
      changes = { 
        'body': task.body + appendage, 
        'project': new_project,
        'sort_date': str(task.created_at + timedelta(days=1, hours=2, seconds=15)),
      }
      response = self.app.put('%s%s/' % (TASK_PATH, task_id), params=changes)
      self.assertEqual('200 OK', response.status)
      task_dict = json.loads(response.body)['task']
      self.assertEqual(changes['body'], task_dict['body'], "New body should reflect changes, but was %s!" % repr(task_dict['body']))
      self.assertEqual(changes['project'], task_dict['project'], "New project should reflect changes!")
      self.assertEqual(changes['sort_date'], task_dict['sort_date'], "New sort date was not absorbed")
      self.assertTrue(old_updated_at != task_dict['updated_at'], "New updated_at should be different but were %s and %s" % (old_updated_at, task_dict['updated_at']))
      
      response = self.app.get('%s%s/' % (TASK_PATH, task_id))
      self.assertEqual('200 OK', response.status)
      task_dict = json.loads(response.body)['task']
      self.assertEqual(changes['body'], task_dict['body'], "New body should reflect changes, but was %s!" % repr(task_dict['body']))
      self.assertEqual(changes['project'], task_dict['project'], "New project should reflect changes!")
      self.assertEqual(changes['sort_date'], task_dict['sort_date'], "New sort date was not absorbed")
      self.assertTrue(old_updated_at != task_dict['updated_at'], "New updated_at should be different but were %s and %s" % (old_updated_at, task_dict['updated_at']))
      
    another_user = TasksUser.gql('WHERE user=:1', users.User(ANOTHER_USER_ADDRESS)).get()
    tasks = Task.gql('where ancestor is :user',user=another_user).fetch(1000)
    self.assertTrue(len(tasks) > 0, "There should be some tasks from another user.")
    for task in tasks:
      appendage = "here's something added to the task body!"
      changes = { 
        'body': task.body + appendage,
      }
      task_id = str(task.key().id())
      response = self.app.put('%s%s/' % (TASK_PATH, task_id), expect_errors=True, params=changes)
      self.assertEqual('404 Not Found', response.status, "Should not allow PUT against another person's tasks")
  
  def test_put_task_archived(self):
    task_list = TaskList.gql('where ancestor is :user', user=self.dnzo_user).get()
    start = datetime.utcnow()
    
    def tasks_for_list():
      all_tasks_response = self.app.get(TASK_PATH, params={ 'task_list': task_list.short_name })
      return json.loads(all_tasks_response.body)['tasks']
    def archived_tasks_from_now():
      end = datetime.utcnow() + timedelta(seconds=1)
      all_tasks_response = self.app.get(ARCHIVED_PATH, params={ 'start_at': start, 'end_at': end })
      return json.loads(all_tasks_response.body)['tasks']
      
    all_tasks = tasks_for_list()
    
    size = len(all_tasks)
    archived_size = 0
    
    self.assertTrue(size > 0, "Should be some tasks")
    
    for task in all_tasks:
      task_id = task['id']
      
      self.assertTrue(not task['complete'], "Task should not be complete")
      response = self.app.put('%s%s/' % (TASK_PATH, str(task_id)), params={ 'archived': 'true' }, expect_errors=True)
      self.assertTrue('400' in response.status, "Status should be 400 -- can't archive an incomplete task. Was: %s" % response.status)
      
      response = self.app.put('%s%s/' % (TASK_PATH, str(task_id)), params={ 'complete': 'true', 'archived': 'true' })
      self.assertEqual('200 OK', response.status)
      
      new_tasks = tasks_for_list()
      archived_tasks = archived_tasks_from_now()
      
      size -= 1
      archived_size += 1
      
      self.assertEqual(size, len(new_tasks), "New task list length should be one less because we archived a task; was %s" % size)
      self.assertEqual(archived_size, len(archived_tasks), "Archived length should be %s; was %s" % (archived_size, len(archived_tasks)))
      self.assertTrue(task_id not in [t['id'] for t in new_tasks], "New tasks list should not contain the task we just archived.")
      
  def test_archived_tasks(self):
    def archived_tasks_for(start,end):
      all_tasks_response = self.app.get(ARCHIVED_PATH, params={ 'start_at': start, 'end_at': end })
      return json.loads(all_tasks_response.body)['tasks']
    
    bad_ranges = (
      {},
      {'start_at': datetime.utcnow() },
      {'end_at': datetime.utcnow() },
      {'start_at': datetime.utcnow(), 'end_at': 'poop'},
      {'start_at': '12-1234-51', 'end_at': datetime.utcnow() },
      {'start_at': None, 'end_at': None },
      {'end_at': datetime.utcnow() - timedelta(seconds=1), 'start_at': datetime.utcnow() },
    )
      
    for params in bad_ranges:      
      response = self.app.get(ARCHIVED_PATH, params=params, expect_errors=True)
      self.assertTrue('400' in response.status, "Status should be 400 -- must specify start/stop; was: %s" % response.status)
    
    response = self.app.get(ARCHIVED_PATH, params={ 'start_at': datetime.utcnow(), 'end_at': datetime.utcnow() })
    self.assertEqual('200 OK', response.status)
    
    start = datetime.utcnow() - timedelta(seconds=1)
    stop = datetime.utcnow() + timedelta(minutes=1)
    
    self.assertEqual(0, len(archived_tasks_for(start,stop)), "Archived tasks should be empty!")
    
    task_list = TaskList.gql('where ancestor is :user', user=self.dnzo_user).get()
    all_tasks_response = self.app.get(TASK_PATH, params={ 'task_list': task_list.short_name })
    all_tasks = json.loads(all_tasks_response.body)['tasks']
    self.app.put('%s%s/' % (TASK_PATH, str(all_tasks[0]['id'])), params={ 'complete': 'true', 'archived': 'true' })
    
    archived = archived_tasks_for(start,stop)
    self.assertEqual(1, len(archived), "Archived tasks should have one entry.")
    
    self.assertTrue('task_list_name' in archived[0], "Archived task should indicate the task list name it came from")
    
    
  def test_delete_task(self):
    tasks = Task.gql('where ancestor is :user',user=self.dnzo_user).fetch(1000)
    self.assertTrue(len(tasks) > 0, "There should be some tasks from the user.")
    for task in tasks:
      task_id = str(task.key().id())
      
      response = self.app.get('%s%s/' % (TASK_PATH, task_id), expect_errors=True)
      self.assertEqual('200 OK', response.status)
      
      response = self.app.delete('%s%s/' % (TASK_PATH, task_id))
      self.assertEqual('200 OK', response.status)
      
      response = self.app.get('%s%s/' % (TASK_PATH, task_id), expect_errors=True)
      self.assertEqual('404 Not Found', response.status, "Task should be deleted!")
      response = self.app.delete('%s%s/' % (TASK_PATH, task_id), expect_errors=True)
      self.assertEqual('404 Not Found', response.status, "Task should be deleted!")
      
    another_user = TasksUser.gql('WHERE user=:1', users.User(ANOTHER_USER_ADDRESS)).get()
    tasks = Task.gql('where ancestor is :user',user=another_user).fetch(1000)
    self.assertTrue(len(tasks) > 0, "There should be some tasks from another user.")
    for task in tasks:
      task_id = str(task.key().id())
      
      response = self.app.delete('%s%s/' % (TASK_PATH, task_id), expect_errors=True)
      self.assertEqual('404 Not Found', response.status, "Should not allow DELETE against another person's tasks")
      

  def test_updated_since(self):
    tasks = list(Task.gql('where ancestor is :user',user=self.dnzo_user).fetch(1000))
    self.assertTrue(len(tasks) > 0, "There should be some tasks from the user.")
    
    random.shuffle(tasks)
    #logging.info("Shuffled order was: %s" % (", ".join([str(task.key().id()) for task in tasks])))
    
    now = datetime.utcnow()
    
    response = self.app.get(TASK_PATH, params={ 'updated_since': now })
    task_dicts = json.loads(response.body)['tasks']
    self.assertEqual(0, len(task_dicts), "There should be no tasks updated since now.")
    
    old_now = now
    
    for task in tasks:
      task_id = str(task.key().id())
      
      changes = { 'body': task.body + "!!!!!!!" }
      response = self.app.put('%s%s/' % (TASK_PATH, task_id), params=changes)
      self.assertEqual('200 OK', response.status)
      
      response = self.app.get(TASK_PATH, params={ 'updated_since': now })
      task_dicts = json.loads(response.body)['tasks']
      self.assertEqual(1, len(task_dicts), "There should be ONE task updated since now, the one we just changed.")
      
      now = datetime.utcnow()
      
    response = self.app.get(TASK_PATH, params={ 'updated_since': old_now })
    task_dicts = json.loads(response.body)['tasks']
    self.assertTrue(len(task_dicts) != 0, "Tasks should not be empty")
    self.assertEqual(len(tasks), len(task_dicts), "The list of updated tasks should be the same as the number of tasks since we just cahnged all of them.")
    
    # sort order
    latest_updated_at = None
    for task in task_dicts:
      updated_at = parse_datetime(task['updated_at'])
      if latest_updated_at:
        self.assertTrue(updated_at > latest_updated_at)
      latest_updated_at = updated_at


  def test_get_tasks_for_list(self):
    all_tasks_response = self.app.get(TASK_PATH, expect_errors=True)
    self.assertTrue("400 Bad Request" in all_tasks_response.status,
                    "Status should be 400 because we didn't supply any arguments.")
    
    task_list = TaskList.gql('where ancestor is :user', user=self.dnzo_user).get()
    all_tasks_response = self.app.get(TASK_PATH, params={ 'task_list': task_list.short_name })
    
    all_tasks_raw = json.loads(all_tasks_response.body)
    all_tasks = {}
    self.assertTrue('tasks' in all_tasks_raw, "Tasks GET should return a dictionary with 'tasks' in it")
    self.assertTrue('error' not in all_tasks_raw, "Tasks GET should not include an error.")
    for task in all_tasks_raw['tasks']:
      all_tasks[str(task['id'])] = task
    
    self.assertEqual(0, len(filter(lambda t: 'archived' in t, all_tasks_raw['tasks'])), "All tasks shown should be not archived.")
    
    self.assertEqual('200 OK', all_tasks_response.status)

    tasks = Task.gql('where ancestor is :user',user=self.dnzo_user).fetch(1000)
    self.assertTrue(len(tasks) > 0, "There should be some tasks from the user.")
    for task in tasks:
      task_id = str(task.key().id())
      self.assertTrue(task_id in all_tasks, "Task ID should appear in the list of all tasks from before")
      
      response = self.app.get('%s%s/' % (TASK_PATH, task_id))
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
      response = self.app.get('%s%s/' % (TASK_PATH, task_id), expect_errors=True)
      self.assertEqual('404 Not Found', response.status)
      self.assertTrue(task_id not in all_tasks, "Task ID from another user should NOT appear in the list of all tasks from before")

    for bogus_id in BOGUS_IDS:
      response = self.app.get('%s%s/' % (TASK_PATH, bogus_id), expect_errors=True)
      self.assertTrue('404 Not Found' in response.status,
                      "Bogus ID task should be Not Found, but response was (%s)" % response.status)
                      
                      
                      
                      
                      