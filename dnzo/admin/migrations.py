from google.appengine.ext import db

def update_project_slugs(start_key = None):
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
  from util.misc import slugify
  
  tasks = Task.gql('%s ORDER BY __key__ ASC' % wheres, **params).fetch(max_records)
  
  total = 0
  updated = 0
  last_key = None
  for task in tasks:
    if task.project:
      task.project_index = slugify(task.project)
      task.put()
      updated += 1
    last_key = str(task.key())
    total += 1
  
  return (total, updated, last_key)

MIGRATIONS = [
  {
    'name': 'Update project slugs', 
    'slug': 'update_project_slugs', 
    'migration': update_project_slugs
  }
]