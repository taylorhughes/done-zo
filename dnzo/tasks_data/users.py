from google.appengine.api.users import get_current_user
from google.appengine.api import memcache

from tasks_data.models import TasksUser

import tasks_data.counting as counting

def clear_user_memcache(user):
  memcache.delete(key=user.user.email())
  
def set_user_memcache(user, email=None):
  if not email:
    email = user.user.email()
  memcache.set(key=email, value=user)

def users_equal(a,b):
  if a is None and b is None:
    return True
  if a is None or b is None:
    return False
  if a.is_saved() and b.is_saved():
    return a.key().id_or_name() == b.key().id_or_name()
  return False
  
def get_dnzo_user(invalidate_cache=False, google_user=None):
  if google_user is None:
    google_user = get_current_user()
    if not google_user:
      return None
  
  try:
    dnzo_user = memcache.get(key=google_user.email())
  except:
    import logging
    logging.exception("Could not retrieve memcached user.")
    dnzo_user = None
    
  if not dnzo_user or invalidate_cache:
    dnzo_user = TasksUser.gql('WHERE user=:user', user=google_user).get()
    memcache.set(key=google_user.email(), value=dnzo_user)

  return dnzo_user
  
def get_dnzo_user_by_email(email):
  return TasksUser.gql('WHERE email=:email', email=email).get()
  
def request_path_to_save(request):
  return request.path_qs
  
def user_history_changed(user, request):
  return user.most_recent_uri != request_path_to_save(request)
  
def record_user_history(user, request, save=True):
  # If this changes, also change the method above!
  changed = user_history_changed(user, request)
  user.most_recent_uri = request_path_to_save(request)
  if save and changed:
    try:
      save_user(user)
    except:
      import logging
      logging.exception("Could not save user's history; not a big deal.")
  
def save_user(user):
  user.put()
  set_user_memcache(user)
  
def delete_user_and_data(dnzo_user):
  from google.appengine.ext import db
  import tasks_data.counting as counting
  from tasks_data.models import Task, TaskList, Project, Context, Undo
      
  to_delete = [dnzo_user]
  
  for t in Task.gql('WHERE ANCESTOR IS :user',user=dnzo_user):
    if not t.deleted:
      counting.task_deleted(t.archived)
    to_delete.append(t)
    
  for t in TaskList.gql('WHERE ANCESTOR IS :user',user=dnzo_user):
    if not t.deleted:
      counting.list_deleted(t,[])
    to_delete.append(t)
  
  for p in Project.gql('WHERE ANCESTOR IS :user',user=dnzo_user):
    to_delete.append(p)
  for c in Context.gql('WHERE ANCESTOR IS :user',user=dnzo_user):
    to_delete.append(c)
  for u in Undo.gql('WHERE ANCESTOR IS :user',user=dnzo_user):
    to_delete.append(u)
    
  clear_user_memcache(dnzo_user)
    
  def delete_all():
    db.delete(to_delete)
  db.run_in_transaction(delete_all)
  
          
def create_user(current_user, list_name=None, default_tasks=None):
  from tasks_data.task_lists import add_task_list

  # Create a default new list for this user
  new_user = TasksUser(user=current_user, email=current_user.email().lower())
  save_user(new_user)
  
  counting.user_added()

  if list_name:
    # add new list for this user
    tasks_list = add_task_list(new_user, list_name)

    # add new default tasks for this user
    from tasks_data.models import Task
    from tasks_data.tasks  import update_task_with_params, save_task
    for task_dict in (default_tasks or []):
      task = Task(parent=new_user, body='', task_list=tasks_list)
      update_task_with_params(new_user, task, task_dict)
      save_task(new_user, task)
  
  return new_user
  
  
  