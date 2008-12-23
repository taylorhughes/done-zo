from django.conf.urls.defaults import patterns

list_pattern = r'^l/(?P<task_list_name>[a-z0-9_-]+)/'

urlpatterns = patterns('',
  
  (r'^account/$', 'tasks.views.settings'),
  (r'^account/transparent/$', 'tasks.views.transparent_settings'),
  
  #  /username/t/id => specific task
  (r'^t/(?P<task_id>\d+)/$', 'tasks.views.task'),
  (r'^t/$', 'tasks.views.task'),
  #  /username/u/id => undo
  (r'^u/(?P<undo_id>\d+)/$', 'tasks.views.undo'),

  #  /username/p/find/ => project
  (r'^p/find/$', 'tasks.views.find_projects'),
  #  /username/p/find/ => project
  (r'^c/find/$', 'tasks.views.find_contexts'),
  
  #  /username/l/_add/
  (r'^l/_add/$', 'tasks.views.add_list'),

  # /username/l/list_name/purge
  (list_pattern + r'purge/$', 'tasks.views.purge_list'),
  # /username/l/list_name/delete
  (list_pattern + r'delete/$', 'tasks.views.delete_list'),
  #  /username/l/list_name/in/project
  (list_pattern + r'for/(?P<project_index>[a-z_-]+)/$', 'tasks.views.list_index'),
  #  /username/l/list_name/near/context
  (list_pattern + r'at/(?P<context_name>[a-z_-]+)/$', 'tasks.views.list_index'),
  
  # archived list
  (r'^l/_archived/$', 'tasks.views.archived_index'),
  
  #  /username/l/list_name
  (list_pattern + r'$', 'tasks.views.list_index'),
  
  
  (r'^redirect/$', 'tasks.views.redirect'),
)
