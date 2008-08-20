from django.template import Library, Node, Context, loader, resolve_variable
from django.template.defaultfilters import date
from datetime import datetime
import logging

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
    
@register.tag
def sorting_header(parser, token):
  try:
    tag_name, my_name, my_sorting, current_sorting, direction = token.split_contents()
  except ValueError:
    raise template.TemplateSyntaxError, "%r tag requires exactly four arguments" % token.contents.split()[0]
  
  return SortingHeader(my_name[1:-1], my_sorting[1:-1], current_sorting, direction)
  
class SortingHeader(Node):
  def __init__(self, my_name, my_sorting, current_sorting, direction):
    self.my_name = my_name
    self.my_sorting = my_sorting
    self.current_sorting = current_sorting
    self.direction = direction
    
  def render(self, context):
    im_sorted = (resolve_variable(self.current_sorting,context) == self.my_sorting)
    ascending = (resolve_variable(self.direction,context) == 'ASC')
    
    url = "?order=%s" % self.my_sorting
    if im_sorted and ascending:
      url += "&amp;descending=true"
          
    class_names = ''
    if im_sorted:
      class_names = 'sorted'
      if ascending:
        self.my_name += " &uarr;"
      else:
        self.my_name += " &darr;"
        class_names += ' descending'
      class_names = ' class="%s"' % class_names

    return '<th%s><a href="%s">%s</a></th>' % (class_names, url, self.my_name)