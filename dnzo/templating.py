from django import template
from django.template import Library, Node, Context, loader, resolve_variable
from django.template.defaultfilters import date
from datetime import datetime

import environment

register = Library()
    
# STOLEN FROM Django 1.0

_base_js_escapes = (
    ('\\', r'\x5C'),
    ('\'', r'\x27'),
    ('"', r'\x22'),
    ('>', r'\x3E'),
    ('<', r'\x3C'),
    ('&', r'\x26'),
    ('=', r'\x3D'),
    ('-', r'\x2D'),
    (';', r'\x3B')
)

# Escape every ASCII character with a value less than 32.
_js_escapes = (_base_js_escapes +
               tuple([('%c' % z, '\\x%02X' % z) for z in range(32)]))

@register.filter
def escapejs(value):
  """Hex encodes characters for use in JavaScript strings."""
  for bad, good in _js_escapes:
      value = value.replace(bad, good)
  return value
  
@register.filter
def short_date(my_date):
  if not my_date:
    return ""
  
  format = "b j"
  if my_date.year != datetime.utcnow().year:
    format += " y"
  # utilize the default django date filter
  return date(my_date, format)

@register.tag
def javascript_tag(parser, token):
  try:
    tag_name, filename = token.split_contents()
  except ValueError:
    raise template.TemplateSyntaxError, "%r requires exactly one argument." % token.contents.split()[0]
  return JavaScriptTag(filename)
  
@register.tag
def combined_javascript_tag(parser, token):
  ''' {% combined_javascript_tag collection a b c %}
  
      will output a script tag for collection in production,
      but will output a script tag for a, b, and c in development.  '''
   
  tokens = list(token.split_contents())
  tag_name, js_files = tokens[:1], tokens[1:]

  if len(js_files) < 2:
    raise template.TemplateSyntaxError, "%r requires at least 2 arguments." % tag_name
    
  if environment.IS_DEVELOPMENT:
    return TagCollection(JavaScriptTag(js) for js in js_files[1:])
  else:
    return JavaScriptTag(js_files[0])
  
@register.tag
def css_tag(parser, token):
  try:
    tag_name, filename = token.split_contents()
  except ValueError:
    raise template.TemplateSyntaxError, "%r requires exactly one argument." % token.contents.split()[0]
  return CSSTag(filename)
  
class TagCollection(Node):
  def __init__(self, nodes):
    self.nodes = nodes
  def render(self, context):
    return ' '.join(node.render(context) for node in self.nodes)
  
class VersionedTag(Node):
  def __init__(self, filename):
    self.base_filename = filename
  
  @property
  def filename(self):
    if environment.IS_DEVELOPMENT:
      return self.base_filename
    return self.base_filename + "_min"
    
  @property
  def version(self):
    return "r%s" % environment.MAJOR_VERSION
    
class JavaScriptTag(VersionedTag):
  def render(self, context):
    filename = '/javascripts/%s/%s.js' % (self.version, self.filename)
    return '<script type="text/javascript" src="%s"></script>' % filename
    
class CSSTag(VersionedTag):
  def render(self, context):
    filename = '/stylesheets/%s/%s.css' % (self.version, self.filename)
    return '<link rel="stylesheet" href="%s" type="text/css" media="all">' % filename