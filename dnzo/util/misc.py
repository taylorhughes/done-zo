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
  title = title.lower().strip()
  title = re.sub(r'[^a-z0-9\s_-]', '', title)
  title = re.sub(r'\s+', '_',  title)
  return title
  
def is_urlized(string):
  return re.search(r'^[a-z0-9_-]+$', string)