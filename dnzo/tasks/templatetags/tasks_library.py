from django.template import Library, Node, Context, loader
from django.template.defaultfilters import date
from datetime import datetime
import logging

from google.appengine.api.users import create_logout_url

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
def logout_url(parser, token):
  class LogoutUrl(Node):
    def render(self, context):
      return create_logout_url('/')
  return LogoutUrl()