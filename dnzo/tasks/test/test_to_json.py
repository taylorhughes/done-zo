import unittest

from django.utils import simplejson as json
from copy import copy

from tasks_data.models import Task

class ToJSONTestCase(unittest.TestCase):
  
  def setUp(self):
    from tasks.test.fixtures import setup_fixtures
    setup_fixtures()
    
  def test_task(self):
    tasks = Task.all()
    for i, task in enumerate(tasks):
      serialized = task.to_json()
      self.assert_(isinstance(serialized, str), "Serialized form should be a string")
      deserialized = json.loads(serialized)
      self.assertEquals(deserialized['body'], task.body, "Task body should be the same after de-serialization")
    
  def test_task_list(self):
    pass
    
