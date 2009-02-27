# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from google.appengine.api import memcache 
from google.appengine.ext import db
import random

import time

NUM_NEW_USERS      = 'num-users'

NUM_ACTIVE_TASKS   = 'num-active-tasks'
NUM_ARCHIVED_TASKS = 'num-archived'
NUM_TASKS_CREATED  = 'num-tasks-created'

NUM_ACTIVE_LISTS   = 'num-active-lists'
NUM_LISTS_CREATED  = 'num-lists-created'

def task_added():
  increment(NUM_TASKS_CREATED + time.strftime('-%Y-%m'))
  increment(NUM_ACTIVE_TASKS)

def task_deleted():
  decrement(NUM_ACTIVE_TASKS)
def task_undeleted():
  increment(NUM_ACTIVE_TASKS)
  
def list_added():
  increment(NUM_LISTS_CREATED + time.strftime('-%Y-%m'))
  increment(NUM_ACTIVE_LISTS)
  
def list_deleted(list, deleted_tasks):
  decrement(NUM_ACTIVE_LISTS)
  decrement(NUM_ACTIVE_TASKS, len(deleted_tasks))
def list_undeleted(list, deleted_tasks):
  increment(NUM_ACTIVE_LISTS)
  increment(NUM_ACTIVE_TASKS, len(deleted_tasks))

def list_archived(list, archived_tasks):
  decrement(NUM_ACTIVE_TASKS, len(archived_tasks))
  increment(NUM_ARCHIVED_TASKS, len(archived_tasks))
def list_unarchived(list, archived_tasks):
  increment(NUM_ACTIVE_TASKS, len(archived_tasks))
  decrement(NUM_ARCHIVED_TASKS, len(archived_tasks))

def user_added():
  increment(NUM_NEW_USERS)
  increment(NUM_NEW_USERS + time.strftime('-%Y-%m'))


DEFAULT_SHARDS = 5

class GeneralCounterShardConfig(db.Model):
  """Tracks the number of shards for each named counter."""
  name = db.StringProperty(required=True)
  num_shards = db.IntegerProperty(required=True, default=DEFAULT_SHARDS)


class GeneralCounterShard(db.Model):
  """Shards for each named counter"""
  name = db.StringProperty(required=True)
  count = db.IntegerProperty(required=True, default=0)
  
            
def get_count(name):
  """Retrieve the value for a given sharded counter.
  
  Parameters:
    name - The name of the counter  
  """
  total = memcache.get(name)
  if total is None:
    total = 0
    for counter in GeneralCounterShard.all().filter('name = ', name):
      total += counter.count
    memcache.add(name, str(total), 60)
  return total

  
def increment(name,value=1):
  """Increment the value for a given sharded counter.
  
  Parameters:
    name - The name of the counter  
  """
  add_or_subtract(name,value)

def decrement(name,value=1):
  """Increment the value for a given sharded counter.
  
  Parameters:
    name - The name of the counter  
  """
  add_or_subtract(name,-value)
  
def add_or_subtract(name, value=0):
  """Decrement the value for a given sharded counter.
  
  Parameters:
    name - The name of the counter  
  """
  config = GeneralCounterShardConfig.get_or_insert(name, name=name)
  def txn():
    index = random.randint(0, config.num_shards - 1)
    shard_name = "%s-%s" % (name,index)
    counter = GeneralCounterShard.get_by_key_name(shard_name)
    if counter is None:
      counter = GeneralCounterShard(key_name=shard_name, name=name)
    counter.count += value
    counter.put()
  db.run_in_transaction(txn)
  memcache.incr(name)
  
def increase_shards(name, num):  
  """Increase the number of shards for a given sharded counter.
  Will never decrease the number of shards.
  
  Parameters:
    name - The name of the counter
    num - How many shards to use
    
  """
  config = GeneralCounterShardConfig.get_or_insert(name, name=name)
  def txn():
    if config.num_shards < num:
      config.num_shards = num
      config.put()    
  db.run_in_transaction(txn)

