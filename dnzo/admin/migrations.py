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
  }
]