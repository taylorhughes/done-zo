
from tasks_data.models import TaskList, Task

def list_url(task_list=None):
  url = '/l/'
  if not task_list:
    return url
  list_name = task_list
  if isinstance(task_list, TaskList):
    list_name = task_list.short_name
  return '%s%s/' % (url, list_name)
  
def task_url(task=None):
  url = '/t/'
  if not task:
    return url
  task_id = task
  if isinstance(task, Task):
    task_id = task.key().id()
  return '%s%s/' % (url, task_id)
  
URL_TAG_MAPPING = {
  'settings': '/settings/',
  'signup_closed': '/signup/closed.html',
  'redirect': '/signin/',
  'task': task_url,
  'list': list_url,
  'archived_list': list_url('_archived'),
  'add_list': list_url,
  'purge_list': lambda list_name: list_url(list_name) + 'purge',
  'delete_list': lambda list_name: list_url(list_name) + 'delete',
  'list_project': lambda list_name, project: list_url(list_name) + 'for/%s/' % project,
  'list_context': lambda list_name, context: list_url(list_name) + 'at/%s/' % context,
  'list_due': lambda list_name, due: list_url(list_name) + 'on/%s/' % due,
  'transparent_settings': '/settings/transparent',
}

def map_url(*args):
  name = args[0:1][0]
  args = args[1:]
  for k,v in URL_TAG_MAPPING.iteritems():
    if k == name:
      if callable(v):
        return v(*args)
      return v

from api.views import APITasksHandler, APITaskHandler

API_PREFIX = '/api/0.1/'
API_URLS = [
  (API_PREFIX + r't/(?P<task_id>[0-9]+)/?', APITaskHandler),
  (API_PREFIX + r't/?', APITasksHandler),
]

from public.views import WelcomeHandler, SignupHandler, ClosedHandler

PUBLIC_URLS = [
  (r'^/$', WelcomeHandler),
  (r'^/signup/$', SignupHandler),
  (r'^%s$' % map_url('signup_closed'), ClosedHandler),
]

from tasks.views import TaskListHandler, PurgeTaskListHandler, DeleteTaskListHandler, \
  ArchivedListHandler, TaskHandler

list_pattern = r'^/l/(?P<task_list_name>[a-z0-9][a-z0-9_-]*)'
TASKS_URLS = [
  # /l/list_name/
  (r'%s/?$' % list_pattern, TaskListHandler),

  #  /username/l/
  #(r'^l/?$', 'tasks.views.add_list'),

  # /username/l/list_name/delete
  (list_pattern + r'delete/?$', DeleteTaskListHandler),
  
  # archived list
  (r'^/l/_archived/?$', ArchivedListHandler),
  
  #  /l/list_name/in/project
  #  /l/list_name/at/context
  #  /l/list_name/on/12-02-2005
  (list_pattern + r'(?:' + 
                  r'/for/(?P<project_index>[0-9a-z_-]+)|' + 
                  r'/at/(?P<context_name>[0-9a-z_-]+)|' +
                  r'/on/(?P<due_date>\d{2}-\d{2}-\d{2})' + 
                  r')?/?$',
                  TaskListHandler),
                  
  # /username/l/list_name/purge
  (list_pattern + r'/purge/?$', PurgeTaskListHandler),
  
#  (r'^account/$', 'tasks.views.settings'),
#  (r'^account/transparent/$', 'tasks.views.transparent_settings'),
  
  #  /username/t/id => specific task
  (r'^/t/?$', TaskHandler),
  (r'^/t/(?P<task_id>\d+)/?$', TaskHandler),
  #  /username/u/id => undo
#  (r'^u/(?P<undo_id>\d+)/$', 'tasks.views.undo'),
  
  #  /username/l/list_name
#  (list_pattern + r'$', 'tasks.views.list_index'),
    
#  (r'^/signin/$', 'tasks.views.redirect'),
]

ALL_URLS = API_URLS + PUBLIC_URLS + TASKS_URLS

  