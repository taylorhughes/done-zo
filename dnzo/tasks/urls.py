from django.conf.urls.defaults import *

username_pattern = r'^(?P<username>[a-z_-]+)/'
list_pattern = username_pattern + r'l/(?P<task_list>[a-z_-]+)/'

urlpatterns = patterns('',
  (r'^$', 'tasks.views.welcome'),
  (r'^tasks/$', 'tasks.views.redirect'),
  (r'^signup/$', 'tasks.views.signup'),
  
  #  /username/to_do/task/id
  (username_pattern + r't/(?P<task_id>\d+)/$', 'tasks.views.task'),
  (username_pattern + r't/$', 'tasks.views.task'),
  (username_pattern + r'u/(?P<undo_id>\d+)/$', 'tasks.views.undo'),

  # /username/list_name/purge
  (list_pattern + r'purge/$', 'tasks.views.purge_tasks'),
  #  /username/list_name/in/{project}
  (list_pattern + r'for/(?P<project_name>[a-z_-]+)/$', 'tasks.views.tasks_index'),
  #  /username/list_name/near/{context}
  (list_pattern + r'at/(?P<context_name>[a-z_-]+)/$', 'tasks.views.tasks_index'),
  #  /username/to_do
  (list_pattern, 'tasks.views.tasks_index'),
  
  #  /username/
  (username_pattern + r'$', 'tasks.views.lists_index'),
)
