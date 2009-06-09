#
#  util.misc: Miscellaneous convenience methods
#

import re

def param(name, collection, default=None):
  if hasattr(collection, 'get'):
    return collection.get(name, default)
  elif name in collection:
    return str(collection[name]).strip()
  return default
  
def slugify(value):
    """
    Stolen from Django 1.0.2:
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', unicode(value)).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return str(re.sub('[-\s]+', '-', value))
  
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