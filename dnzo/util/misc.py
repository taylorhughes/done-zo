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
  
def slugify(string):
  from django.template.defaultfilters import slugify
  return str(slugify(string))
  
def indexize(string):
  if not string:
    string = ''
  string = string.lower()
  string = re.sub(r'\s+', ' ', string)
  string = re.sub(r'[^0-9a-z\s]+', '', string)
  return string
  
def zpad(string):
  if not string:
    string = ''
  # Append the maximum unicode value.
  return string + u"\ufffd"