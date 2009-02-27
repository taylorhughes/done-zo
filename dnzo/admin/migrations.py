from google.appengine.ext import db

def update_task_counts(start_key = None):
  def fn(task_list):
    from tasks_data.models import Task
  
    active_tasks = Task.gql(
      'WHERE task_list=:task_list AND deleted=:deleted AND archived=:archived',
      task_list=task_list, deleted=False, archived=False
    ).fetch(1000)
    
    archived_tasks = Task.gql(
      'WHERE task_list=:task_list AND deleted=:deleted AND archived=:archived',
      task_list=task_list, deleted=False, archived=True
    ).fetch(1000)
    
    task_list.active_tasks_count = len(active_tasks)
    task_list.archived_tasks_count = len(archived_tasks)
    task_list.put()
    
    return True
    
  from tasks_data.models import TaskList
  return do_for_all(TaskList, start_key, fn, 3)

def update_initial_counts(start_key = None):
  def fn(user):
    from tasks_data.models import Task, TaskList
    import tasks_data.counting as counting
  
    lists = TaskList.gql(
      'WHERE ANCESTOR IS :user AND deleted=:deleted',
      user=user, deleted=False
    ).fetch(1000)
  
    active_tasks = 0
    for task_list in lists:
      tasks = Task.gql(
        'WHERE task_list=:task_list AND deleted=:deleted AND archived=:archived',
        task_list=task_list, deleted=False, archived=False
      ).fetch(1000)
      active_tasks += len(tasks)
    
    archived_tasks = Task.gql(
      'WHERE ANCESTOR IS :user AND deleted=:deleted AND archived=:archived',
      user=user, deleted=False, archived=True
    ).fetch(1000)
    archived_tasks = len(archived_tasks)
    
    counting.increment(counting.NUM_NEW_USERS)
    
    counting.increment(counting.NUM_ACTIVE_TASKS, active_tasks)
    counting.increment(counting.NUM_ARCHIVED_TASKS, archived_tasks)
    
    counting.increment(counting.NUM_ACTIVE_LISTS, len(lists))
    
    return True
    
  from tasks_data.models import TasksUser
  return do_for_all(TasksUser, start_key, fn, 1)

def do_for_all(model_klass, start_key, callback, max_records = 100):
  objects = get_all_from_key(model_klass, start_key, max_records)
  
  total = 0
  updated = 0
  last_key = None
  for obj in objects:
    if callback(obj):
      updated += 1
    total += 1

    last_key = str(obj.key())
  
  return (total, updated, last_key)
  
def get_all_from_key(model_klass, start_key, max_records):  
  params = {}
  wheres = []
  
  if start_key is not None:
    wheres.append('__key__ > :key')
    params['key'] = db.Key(start_key)
  
  if len(wheres) > 0:
    wheres = 'WHERE ' + ' AND '.join(wheres)
  else:
    wheres = ''
  
  return model_klass.gql('%s ORDER BY __key__ ASC' % wheres, **params).fetch(max_records)
  
MIGRATIONS = [
  {
    'name': 'Update task counts', 
    'slug': 'update_task_counts', 
    'migration': update_task_counts
  },
  {
    'name': 'Update initial counters', 
    'slug': 'update_initial_counts', 
    'migration': update_initial_counts
  }
]