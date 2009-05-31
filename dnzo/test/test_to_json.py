import unittest

from django.utils import simplejson as json
from copy import copy

from tasks_data.models import Task

class ToJSONTestCase(unittest.TestCase):
  
  def setUp(self):
    from test.fixtures import setup_fixtures
    setup_fixtures()
    
  def test_task(self):
    tasks = Task.all()
    for i, task in enumerate(tasks):
      dictized = task.to_dict()
      self.assertEquals(dictized, dict(dictized), "Task.to_dict should produce a dict")
      self.assertTrue('body' in dictized, "Dictized version should include the task body")
      serialized = json.dumps(dictized)
      self.assertTrue(isinstance(serialized, str), "Serialized form should be a string")
      deserialized = json.loads(serialized)
      self.assertEquals(deserialized['body'], task.body, "Task body should be the same after de-serialization")
    
  def test_task_list(self):
    pass
    
