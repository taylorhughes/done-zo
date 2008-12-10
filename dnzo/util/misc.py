#
#  util.misc: Miscellaneous convenience methods
#

import re

def param(name, collection, default=None):
  if name in collection:
    return collection[name].strip()
  return default

def is_ajax(request):
  ajax_header = 'HTTP_X_REQUESTED_WITH'
  return (ajax_header in request.META and request.META[ajax_header] == 'XMLHttpRequest')
  
def urlize(title):
  title = title.lower()
  transforms = (
    # Strip blanks from the beginning and end
    (r'^[\s_-]+', ''),
    (r'[\s_-]+$', ''),
    # Replace double -- or __ or -_-_
    (r'[\s_-]{2,}', '_'),
    # Replace any space with a single underscore.
    (r'\s+', '_'),
    # Replace any unallowed chars
    (r'[^a-z0-9\s_-]', ''),
  )
  for find, replace in transforms:
    title = re.sub(find, replace, title)

  return title
  
def is_urlized(string): 
  return re.search(r'^[a-z0-9][a-z0-9_-]+[a-z0-9]$', string) and not \
         re.search(r'[_-]{2,}', string)
         
def indexize(string):
  if not string:
    string = ''
  string = string.lower()
  string = re.sub(r'\s+', ' ', string)
  string = re.sub(r'[^0-9a-z\s]+', '', string)
  return string
  
def zpad(string, length=20):
  if not string:
    string = ''
    
  return string + ('z' * (length - len(string)))