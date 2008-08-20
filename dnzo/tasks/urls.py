from django.conf.urls.defaults import *

username_pattern = r'^(?P<username>[a-z_-]+)/'
list_pattern = username_pattern + r'(?P<task_list>[a-z_-]+)/'

urlpatterns = patterns('',
  (r'^tasks/$', 'tasks.views.redirect'),
  (r'^signup/$', 'tasks.views.signup'),
  (r'^$', 'tasks.views.welcome'),
  #  /username/list_name/in/{project}
  (list_pattern + r'in/(?P<project_name>[a-z_-]+)/$', 'tasks.views.tasks_index'),
  #  /username/list_name/near/{context}
  (list_pattern + r'context/(?P<context_name>[a-z_-]+)/$', 'tasks.views.tasks_index'),
  #  /username/list_name/by/{date}
  #(list_pattern + r'by/(?P<year>20\d{2})_(?P<month>\d{1,2})_(?P<day>\d{1,2})/$', 'tasks.views.date'),
  #  /username/task/id
  #(username_pattern + r'task/(?P<task_key>.+)$', 'tasks.views.task'),
  (list_pattern, 'tasks.views.tasks_index'),
  #  /username/
  (username_pattern + r'$', 'tasks.views.lists_index'),
)
