from django import template
from django.template import Library, Node, Context, loader, resolve_variable
from django.template.defaultfilters import date
from datetime import datetime

import re
import logging

import environment

register = Library()
    
@register.filter
def short_date(my_date):
  if not my_date:
    return ""
  
  format = "b j"
  if my_date.year != datetime.now().year:
    format += " y"
  # utilize the default django date filter
  return date(my_date, format)
        
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
    tag_name, my_name, my_sorting, current_sorting, direction, class_name = token.split_contents()
  except ValueError:
    raise template.TemplateSyntaxError, "%r tag requires exactly four arguments" % token.contents.split()[0]
  
  return SortingHeader(my_name[1:-1], my_sorting[1:-1], current_sorting, direction, class_name[1:-1])
  
class SortingHeader(Node):
  def __init__(self, my_name, my_sorting, current_sorting, direction, class_name):
    self.my_name = my_name
    self.my_sorting = my_sorting
    self.current_sorting = current_sorting
    self.direction = direction
    self.class_name = class_name
    
  def render(self, context):
    im_sorted = (resolve_variable(self.current_sorting,context) == self.my_sorting)
    ascending = (resolve_variable(self.direction,context) == 'ASC')
    
    url = "?order=%s" % self.my_sorting
    if im_sorted and ascending:
      url += "&amp;descending=true"
          
    class_names = []
    
    if self.class_name:
      class_names.append(self.class_name)
      
    if im_sorted:
      class_names.append('sorted')
      if not ascending:
        class_names.append('descending')
    
    if len(class_names) > 0:
      class_names = ' class="%s"' % (' '.join(class_names))
    else:
      class_names = ''

    return '<th><a href="%s"%s>%s</a></th>' % (url, class_names, self.my_name)
    
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
    return self.base_filename + "_compiled"
    
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
    return '<link rel="stylesheet" href="%s" type="text/css" media="all" />' % filename