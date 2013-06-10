from django import template
from django.template import Library, Node

register = Library()

@register.filter
def adjust_date(my_date, user):
  from datetime import timedelta

  return my_date - timedelta(minutes=user.timezone_offset_mins)
  
  
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
    