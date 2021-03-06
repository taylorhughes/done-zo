from tasks_data.models import TaskList, Task

from api.views import APITasksHandler, APITaskHandler, APITaskListHandler, \
                      APITaskListsHandler, APIResetAccountHandler, \
                      APIArchivedTasksHandler

API_PREFIX = r'/api/0.1/'
API_URLS = [
  (API_PREFIX + r't/<:[0-9]+>/', APITaskHandler),
  (API_PREFIX + r't/', APITasksHandler),
  (API_PREFIX + r'l/<:[a-z0-9][a-z0-9_-]*>/', APITaskListHandler),
  (API_PREFIX + r'l/', APITaskListsHandler),
  (API_PREFIX + r'l', APITaskListsHandler),
  (API_PREFIX + r'a/', APIArchivedTasksHandler),
  (API_PREFIX + r'reset_account/', APIResetAccountHandler),
]

from public.views import MaintenanceWelcomeHandler, MaintenanceHandler

MAINTENANCE_URLS = [
  (r'/', MaintenanceWelcomeHandler),
  (r'/.+', MaintenanceHandler),
]

from public.views import WelcomeHandler, AboutHandler, SignupHandler, ClosedHandler

PUBLIC_URLS = [
  (r'/', WelcomeHandler),
  (r'/about/', AboutHandler),
  (r'/signup/', SignupHandler),
  (r'/signup/closed.html', ClosedHandler),
]

from tasks.views import TaskListHandler, ProjectTaskListHandler, \
  ContextTaskListHandler, DueTaskListHandler, AddTaskListHandler, \
  PurgeTaskListHandler, DeleteTaskListHandler, ArchivedListHandler, \
  TransparentSettingsHandler, SettingsHandler, RedirectHandler, \
  NewTaskHandler, TaskHandler, UndoHandler, NoopHandler

list_pattern = r'/l/<:[a-z0-9][a-z0-9_-]*>'
TASKS_URLS = [  
  #  /l/
  (r'/l/', AddTaskListHandler),
  
  # archived list
  (r'/l/_archived/', ArchivedListHandler),
  
  # /l/list_name
  # /l/list_name/for/project
  # /l/list_name/at/context
  # /l/list_name/on/12-02-2005
  (list_pattern + r'/',TaskListHandler),
  # we can't use named parameters to differentiate urls so they need different handlers:
  (list_pattern + r'/for/<:[0-9a-z_-]+>/', ProjectTaskListHandler),
  (list_pattern + r'/at/<:[0-9a-z_-]+>/', ContextTaskListHandler),
  (list_pattern + r'/on/<:\d{2}-\d{2}-\d{2}>/', DueTaskListHandler),

  # /username/l/list_name/delete
  (list_pattern + r'/delete/', DeleteTaskListHandler),
  
  # /l/list_name/purge
  (list_pattern + r'/purge/', PurgeTaskListHandler),
  
  (r'/account/', SettingsHandler),
  (r'/account/transparent/', TransparentSettingsHandler),
  (r'/account/noop/', NoopHandler),
  
  #  /username/t/id => specific task
  (r'/t/<:\d+>/', TaskHandler),
  (r'/t/', NewTaskHandler),

  #  /u/id => undo
  (r'/u/<:\d+>/', UndoHandler),
  
  (r'/signin/', RedirectHandler),
]

ALL_URLS = API_URLS + PUBLIC_URLS + TASKS_URLS
#ALL_URLS = MAINTENANCE_URLS
  