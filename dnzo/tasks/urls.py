from django.conf.urls.defaults import *

username_pattern = r'^(?P<username>[a-z_-]+)/'
list_pattern = username_pattern + r'(?P<task_list>[a-z_-]+)/'

urlpatterns = patterns('',
  (r'^$', 'tasks.views.welcome'),
  (r'^tasks/$', 'tasks.views.redirect'),
  (r'^signup/$', 'tasks.views.signup'),
  #  /username/list_name/in/{project}
  (list_pattern + r'for/(?P<project_name>[a-z_-]+)/$', 'tasks.views.tasks_index'),
  #  /username/list_name/near/{context}
  (list_pattern + r'at/(?P<context_name>[a-z_-]+)/$', 'tasks.views.tasks_index'),
  #  /username/list_name/by/{date}
  #(list_pattern + r'by/(?P<year>20\d{2})_(?P<month>\d{1,2})_(?P<day>\d{1,2})/$', 'tasks.views.date'),
  #  /username/to_do/task/id
  (list_pattern + r'task/(?P<task_key>\d+)/$', 'tasks.views.task'),
  (list_pattern + r'task/$', 'tasks.views.task'),
  # /username/to_do/purge_tasks
  (list_pattern + r'purge_tasks/$', 'tasks.views.purge_tasks'),
  #  /username/to_do
  (list_pattern, 'tasks.views.tasks_index'),
  #  /username/
  (username_pattern + r'$', 'tasks.views.lists_index'),
)
