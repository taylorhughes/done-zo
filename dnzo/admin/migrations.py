from google.appengine.ext import db

def update_context_indexes(start_key = None):
  def fn(task):
    task.contexts_index = " ".join(task.contexts)
    task.put()
    
    return True
    
  from tasks_data.models import Task
  return do_for_all(Task, start_key, fn, 20)


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
    'name': 'Update context indexes', 
    'slug': 'update_context_indexes', 
    'migration': update_context_indexes
  }
]