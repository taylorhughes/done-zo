from google.appengine.ext import db

def update_created_at(start_key = None):
  max_records = 100
  
  params = {}
  wheres = []
  
  if start_key is not None:
    wheres.append('__key__ > :key')
    params['key'] = db.Key(start_key)
  
  if len(wheres) > 0:
    wheres = 'WHERE ' + ' AND '.join(wheres)
  else:
    wheres = ''
  
  from tasks_data.models import Task
  
  tasks = Task.gql('%s ORDER BY __key__ ASC' % wheres, **params).fetch(max_records)
  
  total = 0
  updated = 0
  last_key = None
  for task in tasks:
    task.real_created_at = task.created_at
    task.put()

    updated += 1
    total += 1

    last_key = str(task.key())
  
  return (total, updated, last_key)
  
MIGRATIONS = [
  {
    'name': 'Update real crated_at times', 
    'slug': 'update_created_at', 
    'migration': update_created_at
  }
]