
from tasks_data.models     import Task
from tasks_data.tasks      import get_tasks, RESULT_LIMIT
from tasks_data.users      import get_dnzo_user, record_user_history, user_history_changed
from tasks_data.task_lists import get_task_list, get_task_lists, can_add_list
  
import environment
from google.appengine.api.users import create_logout_url

import logging

#### VIEWS ####

from dnzo_request_handler import DNZORequestHandler, dnzo_login_required

def operates_on_task_list(fn):
  @dnzo_login_required
  def wrapper(self, task_list_name, *args, **kwargs):
    task_list = get_task_list(self.dnzo_user, task_list_name)
    if not task_list or task_list.deleted:
      if not user_history_changed(self.dnzo_user, self.request):
        self.default_list_redirect()
      else:
        self.not_found()
    else:
      fn(self, task_list, *args, **kwargs)

  return wrapper

class DNZOLoggedInRequestHandler(DNZORequestHandler):
  def always_includes(self, is_handling_error):
    previous = super(DNZOLoggedInRequestHandler,self).always_includes(is_handling_error)

    task_lists = []
    can_add = False
    if not is_handling_error:
      task_lists = get_task_lists(self.dnzo_user)
      can_add = can_add_list(self.dnzo_user)
      
    previous.update({
      'request_uri': self.request.url,
      'task_lists': task_lists,
      'can_add_list': can_add,
      'is_production': environment.IS_PRODUCTION,
      'max_records': RESULT_LIMIT,
      'logout_url': create_logout_url('/'),
    })
    return previous

class TaskListHandler(DNZOLoggedInRequestHandler):
  @operates_on_task_list
  def get(self, task_list, project_index=None, context_name=None, due_date=None):
    record_user_history(self.dnzo_user, self.request)
  
    # FILTER 
    filter_title = None
    view_project = None
    view_project_name = None
    if project_index:
      from tasks_data.misc import get_project_by_short_name
      view_project_name = get_project_by_short_name(self.dnzo_user, project_index)
      if view_project_name:
        filter_title = view_project_name
        view_project = project_index
      else:
        self.list_redirect(task_list)
        return
        
    view_context = None
    if context_name:
      view_context = context_name
      filter_title = "@%s" % context_name
    view_date = None
    if due_date:
      from util.human_time import parse_date
    
      view_date = parse_date(due_date)
      if view_date:
        filter_title = view_date.strftime('%m-%d-%Y')

    tasks = get_tasks(self.dnzo_user, 
                      task_list=task_list, 
                      context=view_context, 
                      project_index=view_project, 
                      due_date=view_date)
  
    # SHOW STATUS MESSAGE AND UNDO
    status, undo = self.get_status_undo()
    
    new_task_attrs = {'body': '', 'parent': self.dnzo_user}
    if view_context:
      new_task_attrs['contexts'] = [view_context]
    if view_project:
      new_task_attrs['project'] = view_project_name
    if view_date:
      new_task_attrs['due_date'] = view_date
  
    new_task = Task(**new_task_attrs)
    new_task.editing = True
    
    self.render('tasks/index.html', 
      tasks=tasks,
      task_list=task_list,
      filter_title=filter_title,
      status=status,
      undo=undo,
      new_tasks=[new_task],
    )
    
class ProjectTaskListHandler(TaskListHandler):
  def get(self,task_list_name,arg):
    super(ProjectTaskListHandler,self).get(task_list_name,project_index=arg)
    
class ContextTaskListHandler(TaskListHandler):
  def get(self,task_list_name,arg):
    super(ContextTaskListHandler,self).get(task_list_name,context_name=arg)
    
class DueTaskListHandler(TaskListHandler):
  def get(self,task_list_name,arg):
    super(DueTaskListHandler,self).get(task_list_name,due_date=arg)
  
class PurgeTaskListHandler(DNZOLoggedInRequestHandler):
  @operates_on_task_list
  def post(self, task_list, project_index=None, context_name=None, due_date=None):
    from tasks_data.task_lists import archive_tasks
    from tasks_data.misc import create_undo
    from statusing import Statuses
  
    undo = None
    status = None

    archived_tasks = archive_tasks(task_list)
    if len(archived_tasks) == 0:
      status = Statuses.TASKS_NOT_PURGED
    else:
      undo = create_undo(self.dnzo_user, task_list=task_list, archived_tasks=archived_tasks)
      status = Statuses.TASKS_PURGED
  
    if status or undo:
      self.set_status_undo(status,undo)
      
    self.referer_redirect()
    
  @operates_on_task_list
  def get(self, *args, **kwargs):
    self.referer_redirect()
    
class DeleteTaskListHandler(DNZOLoggedInRequestHandler):
  @operates_on_task_list
  def get(self, task_list):
    from tasks_data.task_lists import delete_task_list
    from tasks_data.misc import create_undo
  
    undo = None
    if len(get_task_lists(self.dnzo_user)) > 1:
      delete_task_list(self.dnzo_user, task_list)
      undo = create_undo(
        self.dnzo_user,
        request=self.request,
        task_list=task_list,
        list_deleted=True,
        return_uri=self.referer_uri()
      )
    
    if undo and undo.is_saved():
      from statusing import Statuses
      self.set_status_undo(Statuses.LIST_DELETED, undo)
  
    self.default_list_redirect()

  @operates_on_task_list
  def post(self, task_list):
    self.get(task_list)
    
class AddTaskListHandler(DNZOLoggedInRequestHandler):
  @dnzo_login_required
  def get(self):
    if self.is_ajax():
      self.render('tasks/lists/add.html')
    else:
      self.referer_redirect()
    
  @dnzo_login_required    
  def post(self):
    from tasks_data.task_lists import add_task_list
    from util.misc import slugify
  
    new_name = self.request.get('name', '')
    new_list = None
    if len(slugify(new_name)) > 0:
      new_list = add_task_list(self.dnzo_user, new_name)
      if new_list:
        self.list_redirect(new_list)
        return
        
    self.referer_redirect()
    
class SettingsHandler(DNZOLoggedInRequestHandler):
  @dnzo_login_required
  def get(self):
    self.render('tasks/settings.html')
    
  @dnzo_login_required    
  def post(self):
    from tasks_data.users import save_user
    
    self.dnzo_user.hide_project  = self.request.get('show_project',  None) is None
    self.dnzo_user.hide_contexts = self.request.get('show_contexts', None) is None
    self.dnzo_user.hide_due_date = self.request.get('show_due_date', None) is None
    
    save_user(self.dnzo_user)
    
    self.referer_redirect()
  
class TransparentSettingsHandler(DNZOLoggedInRequestHandler):
  @dnzo_login_required
  def post(self):
    from tasks_data.users import save_user
  
    offset = self.request.get('offset', None)
    try:
      self.dnzo_user.timezone_offset_mins = int(offset)
      save_user(self.dnzo_user)
    
    except:
      import logging
      logging.error("Couldn't update timezone offset to %s" % offset)
  
    if self.is_ajax():
      self.render_text("OK")
    else:
      self.referer_redirect()

class ArchivedListHandler(DNZOLoggedInRequestHandler):
  @dnzo_login_required
  def get(self):
    record_user_history(self.dnzo_user, self.request)
    
    from util.human_time import parse_date, HUMAN_RANGES
  
    offset=0
    if self.dnzo_user.timezone_offset_mins:
      offset = self.dnzo_user.timezone_offset_mins
  
    given_range  = self.request.get('range', None)

    start = self.request.get('start', None)
    start = parse_date(start, self.dnzo_user.timezone_offset_mins or 0, output_utc=True)
    stop  = self.request.get('stop', None)
    stop  = parse_date(stop,  self.dnzo_user.timezone_offset_mins or 0, output_utc=True)

    filter_title = None
    if start is not None and stop is not None:
      from django.template.defaultfilters import date
    
      filter_title = '%s to %s' % (date(start,'n-j-y'), date(stop,'n-j-y'))

    else:
      range_slugs = [r['slug'] for r in HUMAN_RANGES]
      try:
        index = range_slugs.index(given_range)
      except:
        given_range = 'this-week'
        index = range_slugs.index(given_range)
      
      start, stop  = HUMAN_RANGES[index]['range'](offset)
      filter_title = HUMAN_RANGES[index]['name']
  
    from tasks_data.tasks import get_archived_tasks
    tasks = get_archived_tasks(self.dnzo_user, start, stop)
    
    self.render('tasks/archived.html',
      tasks=tasks,
      stop=stop,
      start=start,
      ranges=HUMAN_RANGES,
      chosen_range=given_range,
      filter_title=filter_title
    )
    
class TaskHandler(DNZOLoggedInRequestHandler):
  @dnzo_login_required
  def get(self, task_id=None):
    self.post(task_id)
  
  @dnzo_login_required
  def post(self, task_id=None):
    if task_id:
      task = Task.get_by_id(int(task_id), parent=self.dnzo_user)
      if not task:
        self.not_found()
        return
    else:
      task = Task(parent=self.dnzo_user, body='')
    
    from tasks_data.tasks import update_task_with_params, save_task
    
    force_complete   = self.request.get('force_complete', None)
    force_uncomplete = self.request.get('force_uncomplete', None)
    force_delete     = self.request.get('delete', None)
  
    task_above = self.request.get('task_above', None)
    task_below = self.request.get('task_below', None)
  
    status = None
    undo = None
  
    if force_complete or force_uncomplete:
      if force_complete:
        from datetime import datetime
        task.complete = True
        task.completed_at = datetime.utcnow()
      if force_uncomplete: 
        task.complete = False
        task.completed_at = None
    
      save_task(self.dnzo_user, task)

      task = None
        
    elif force_delete:
      from tasks_data.tasks import delete_task
      from tasks_data.misc import create_undo
      from tasks.statusing import get_status_message, Statuses
      status = get_status_message(Statuses.TASK_DELETED)
      delete_task(self.dnzo_user,task)
      undo = create_undo(self.dnzo_user, task_list=task.task_list, deleted_tasks=[task])

      task = None
    
    elif task_above is not None or task_below is not None:
      before, after = None, None
      if task_above:
        task_above = Task.get_by_id(int(task_above), parent=self.dnzo_user)
        if task_above:
          before = task_above.created_at
      if task_below:
        task_below = Task.get_by_id(int(task_below), parent=self.dnzo_user)
        if task_below:
          after = task_below.created_at
        
      from datetime import datetime, timedelta
      new_sort = None  
      if before and after:
        new_sort = before + ((after - before) / 2)
      elif before:
        # last task
        new_sort = datetime.utcnow()
      elif after:
        # first task
        new_sort = after - timedelta(hours=1)
    
      if new_sort:
        task.created_at = new_sort
        save_task(self.dnzo_user, task)
      
      task = None
    
    else:
      update_task_with_params(self.dnzo_user, task, self.request)

      task_list = self.request.get('task_list', None) 
      task_list = task_list and get_task_list(self.dnzo_user, task_list)
      if task_list:
        task.task_list = task_list
      elif not task.task_list:
        self.not_found()
        return

      save_task(self.dnzo_user, task)
  
    if undo:
      undo = undo.key().id()
  
    from environment import IS_DEVELOPMENT
    if IS_DEVELOPMENT:
      # simulate this call taking longer as is normal in production
      from time import sleep
      from random import random
      sleep(2)
  
    if not self.is_ajax():
      self.referer_redirect()
    
    else:
      self.render('tasks/tasks/ajax_task.html',
        user=self.dnzo_user,
        task=task,
        status=status,
        undo=undo,
        task_list=(task and task.task_list)
      )

class NoopHandler(DNZOLoggedInRequestHandler):
  def get(self):
    self.render_text('DNZO-OK')

class UndoHandler(DNZOLoggedInRequestHandler):
  def get(self, undo_id):
    from tasks_data.models import Undo
    from tasks_data.misc import do_undo
    from tasks_data.users import users_equal

    try:
      undo = Undo.get_by_id(int(undo_id), parent=self.dnzo_user)
      
      if undo:
        if not users_equal(undo.parent(), self.dnzo_user):
          self.access_error_redirect()
          return
        do_undo(self.dnzo_user, undo)
          
    except:
      logging.exception("Error undoing!")
    
    if undo.return_uri:
      self.redirect(undo.return_uri)
    else:
      self.referer_redirect()

class RedirectHandler(DNZOLoggedInRequestHandler):
  def get(self):
    if self.dnzo_user:
      self.most_recent_redirect()
    else:
      self.redirect_to('SignupHandler')
      
      
      
      