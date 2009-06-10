
from tasks_data.models import TaskList, Task

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
  (r'^/signup/closed.html$', ClosedHandler),
]

from tasks.views import TaskListHandler, AddTaskListHandler, PurgeTaskListHandler, \
  DeleteTaskListHandler, ArchivedListHandler, TaskHandler, TransparentSettingsHandler, \
  SettingsHandler, RedirectHandler, UndoHandler

list_pattern = r'^/l/(?P<task_list_name>[a-z0-9][a-z0-9_-]*)'
TASKS_URLS = [  
  #  /l/
  (r'^/l/?$', AddTaskListHandler),
  # /l/list_name/
  (list_pattern + r'/?$', TaskListHandler),

  # /username/l/list_name/delete
  (list_pattern + r'/delete/?$', DeleteTaskListHandler),
  
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
  
  (r'^/account/?$', SettingsHandler),
  (r'^/account/transparent/?$', TransparentSettingsHandler),
  
  #  /username/t/id => specific task
  (r'^/t/(?P<task_id>\d+)/?', TaskHandler),
  (r'^/t/$', TaskHandler),

  #  /u/id => undo
  (r'^/u/(?P<undo_id>\d+)/$', UndoHandler),
  
  (r'^/signin/?$', RedirectHandler),
]

ALL_URLS = API_URLS + PUBLIC_URLS + TASKS_URLS

  