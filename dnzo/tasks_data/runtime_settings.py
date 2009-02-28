from google.appengine.api import memcache 
from google.appengine.ext import db

class GeneralSetting(db.Model):
  name  = db.StringProperty(required=True)
  value = db.StringProperty()

def find_all():
  return GeneralSetting.all().fetch(100)

def get_setting(name, default=None):
  """Retrieve the value for a given setting.
  
  Parameters:
    name - The name of the setting
  """
  value = memcache.get(name)
  if value is None:
    setting = GeneralSetting.get_by_key_name(name)
    if setting:
      value = setting.value
      memcache.set(name + '-setting', value)
    else:
      value = default
      set_setting(name, value)
      
  return value

def set_setting(name, value):
  """Set a setting value.
  
  Parameters:
    name - The name of the counter  
  """
  config = GeneralSetting.get_or_insert(name, name=name)
  config.value = value
  config.put()
  
  memcache.set(name + '-setting', value)