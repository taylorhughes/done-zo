from django import template
from django.template import Library, Node, Context, loader, resolve_variable
from django.template.defaultfilters import date
from datetime import datetime

import re

import environment

register = Library()
    
@register.filter
def short_date(my_date):
  if not my_date:
    return ""
  
  format = "b j"
  if my_date.year != datetime.utcnow().year:
    format += " y"
  # utilize the default django date filter
  return date(my_date, format)

@register.filter
def adjust_date(my_date, user):
  from datetime import timedelta

  return my_date - timedelta(minutes=user.timezone_offset_mins)
        
@register.filter
def spans_around(string, to_highlight):
  if not string or not to_highlight:
    return ""

  to_highlight = re.sub(r'\s+', ' ', to_highlight)
  string = re.sub(r'\s+', ' ', string)
    
  regex = '\s*'.join(list(to_highlight))
  regex = re.compile(regex, re.IGNORECASE)
  
  return re.sub(regex, '<span>\g<0></span>', string)
    
@register.tag
def sorting_header(parser, token):
  try:
    tag_name, my_name, my_sorting = token.split_contents()
  except ValueError:
    raise template.TemplateSyntaxError, "%r tag requires exactly four arguments" % token.contents.split()[0]
  
  return SortingHeader(my_name[1:-1], my_sorting[1:-1])
  
class SortingHeader(Node):
  def __init__(self, my_name, my_sorting):
    self.my_name = my_name
    self.my_sorting = my_sorting
    
  def render(self, context):
    url = "#order=%s" % self.my_sorting
          
    return '<th class="%s"><a href="%s">%s</a></th>' % (self.my_sorting, url, self.my_name)
    
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
   
  tokens = list(token.split_contents()[1:])

  if len(tokens) < 2:
    raise template.TemplateSyntaxError, "%r requires at least 2 arguments." % token.contents.split()[0]
    
  if environment.IS_DEVELOPMENT:
    return TagCollection(map(lambda f: JavaScriptTag(f), tokens[1:]))
  else:
    return JavaScriptTag(tokens[0])
  
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
    return ' '.join(map(lambda n: n.render(context), self.nodes))
  
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