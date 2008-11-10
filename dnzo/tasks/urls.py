from django.conf.urls.defaults import *

username_pattern = r'^(?P<username>[a-z0-9_-]+)/'
list_pattern = username_pattern + r'l/(?P<task_list_name>[a-z0-9_-]+)/'

urlpatterns = patterns('',
  (r'^$', 'tasks.views.welcome'),
  (r'^tasks/$', 'tasks.views.redirect'),
  (r'^signup/$', 'tasks.views.signup'),
  (r'^signup/availability/$', 'tasks.views.availability'),
  
  #  /username/t/id => specific task
  (username_pattern + r't/(?P<task_id>\d+)/$', 'tasks.views.task'),
  (username_pattern + r't/$', 'tasks.views.task'),
  #  /username/u/id => undo
  (username_pattern + r'u/(?P<undo_id>\d+)/$', 'tasks.views.undo'),

  #  /username/l/_add/
  (username_pattern + r'l/_add/$', 'tasks.views.add_list'),

  # /username/l/list_name/purge
  (list_pattern + r'purge/$', 'tasks.views.purge_list'),
  # /username/l/list_name/delete
  (list_pattern + r'delete/$', 'tasks.views.delete_list'),
  #  /username/l/list_name/in/project
  (list_pattern + r'for/(?P<project_index>[a-z_-]+)/$', 'tasks.views.list_index'),
  #  /username/l/list_name/near/context
  (list_pattern + r'at/(?P<context_name>[a-z_-]+)/$', 'tasks.views.list_index'),
  #  /username/l/list_name
  (list_pattern, 'tasks.views.list_index'),
  
  (username_pattern, 'tasks.views.redirect'),
)
