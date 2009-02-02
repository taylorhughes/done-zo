from google.appengine.ext import db

def update_mru_lists(start_key = None):
  def fn(user):
    from tasks_data.models import ProjectIndex, Context
    
    contexts = Context.gql('WHERE ANCESTOR IS :user', user=user).fetch(200)
    contexts.sort(key=lambda c: c.last_used_at)
    contexts.reverse()
    user.mru_contexts = map(lambda c: c.name, contexts)
    
    projects = ProjectIndex.gql('WHERE ANCESTOR IS :user', user=user).fetch(200)
    projects.sort(key=lambda p: p.last_used_at)
    projects.reverse()
    projects = map(lambda p: p.name, projects)
    projects_new = []
    for project in projects:
      if project not in projects_new:
        projects_new.append(project)
    user.mru_projects = projects_new
    
    from tasks_data.users import save_user
    save_user(user)
    
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
    'name': 'Create MRU contexts/projects', 
    'slug': 'update_mru_lists', 
    'migration': update_mru_lists
  }
]