from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
  (r'^t/(?:(?P<task_id>\d+)/)?$', 'api.views.task'),
  (r'^l/(?:(?P<task_list_name>[a-z0-9_-]+)/)?$', 'api.views.task_list'),
)