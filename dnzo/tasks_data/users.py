from google.appengine.api.users import get_current_user
from google.appengine.api import memcache

from tasks_data.models import TasksUser

def clear_user_memcache(user):
  memcache.delete(key=user.user.email())
  
def set_user_memcache(user):
  memcache.set(key=user.user.email(), value=user)

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
  
def save_user(user):
  user.put()
  set_user_memcache(user)