from django.shortcuts import render_to_response
from django.http import Http404
from django.views.decorators.cache import never_cache

from tasks_data.models     import Task
from tasks_data.users      import get_dnzo_user, record_user_history
from tasks_data.task_lists import get_task_list, get_task_lists

from tasks.redirects import default_list_redirect, most_recent_redirect, list_redirect, access_error_redirect, referer_redirect
from tasks.statusing import get_status_undo, set_status_undo, reset_status_undo

from util.misc       import param, is_ajax, slugify

SORTABLE_LIST_COLUMNS = ('complete', 'project_index', 'body', 'due_date', 'created_at', 'context')

RESULT_LIMIT = 100

#### VIEWS ####

@never_cache
def list_index(request, task_list_name=None, context_name=None, project_index=None, due_date=None):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
  
  task_list = get_task_list(user, task_list_name)
  if not task_list or task_list.deleted:
    raise Http404

  record_user_history(user, request)
  
  # FILTER 
  filter_title = None
  view_project = None
  view_project_name = None
  if project_index:
    from tasks_data.misc import get_project_by_short_name
    view_project_name = get_project_by_short_name(user, project_index)
    if view_project_name:
      filter_title = view_project_name
      view_project = project_index
    else:
      return list_redirect(user, task_list)
  view_context = None
  if context_name:
    view_context = context_name
    filter_title = "@%s" % context_name
  view_date = None
  if due_date:
    from util.human_time import parse_date
    from django.template.defaultfilters import date
    
    view_date = parse_date(due_date)
    if view_date:
      filter_title = date(view_date, 'n-j-y')

  wheres = ['task_list=:task_list AND archived=:archived'] 
  params = { 'task_list': task_list, 'archived': False }

  if view_context:
    wheres.append('contexts=:context')
    params['context'] = view_context
  elif view_project:
    wheres.append('project_index=:project_index')
    params['project_index'] = view_project
  elif view_date:
    wheres.append('due_date=:due_date')
    params['due_date'] = view_date
    
  default_order, default_direction = 'created_at', 'ASC'
  
  order = str(param('order', request.GET))
  if order in SORTABLE_LIST_COLUMNS:
    direction = 'ASC'
    if param('descending', request.GET) == 'true':
      direction = 'DESC'
    
    order_by = '%s %s, %s %s' % (order, direction, default_order, default_direction)
    is_sortable = False
  
  else:
    order, direction = default_order, default_direction
    order_by = '%s %s' % (order, direction)
    is_sortable = True
  
  gql = 'WHERE %s ORDER BY %s' % (' AND '.join(wheres), order_by)
  tasks = Task.gql(gql, **params).fetch(RESULT_LIMIT)
  
  # SHOW STATUS MESSAGE AND UNDO
  status, undo = get_status_undo(request)
  
  new_task_attrs = {'body': '', 'parent': user}
  if view_context:
    new_task_attrs['contexts'] = [view_context]
  if view_project:
    new_task_attrs['project'] = view_project_name
  if view_date:
    new_task_attrs['due_date'] = view_date
  
  new_task = Task(**new_task_attrs)
  new_task.editing = True
    
  response = render_to_response('tasks/index.html', always_includes({
    'tasks': tasks,
    'task_list': task_list,
    'filter_title': filter_title,
    'order': order,
    'direction': direction,
    'status': status,
    'undo': undo,
    'new_task': new_task,
    'is_sortable': is_sortable,
  }, request, user))
  
  reset_status_undo(response,status,undo)
  
  return response

@never_cache
def archived_index(request, task_list_name=None, context_name=None, project_index=None):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()

  from util.human_time import parse_date, HUMAN_RANGES
  
  offset=0
  if user.timezone_offset_mins:
    offset = user.timezone_offset_mins
  
  given_range  = param('range', request.GET, None)

  start = param('start', request.GET, None)
  start = parse_date(start, user.timezone_offset_mins or 0, output_utc=True)
  stop  = param('stop', request.GET, None)
  stop  = parse_date(stop,  user.timezone_offset_mins or 0, output_utc=True)

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
  
  gql = 'WHERE ANCESTOR IS :user AND archived=:archived AND deleted=:deleted ' + \
        'AND completed_at >= :start AND completed_at < :stop ORDER BY completed_at DESC'

  tasks = Task.gql(gql, 
    user=user,
    archived=True,
    deleted=False,
    start=start,
    stop=stop
  ).fetch(RESULT_LIMIT)
    
  return render_to_response('tasks/archived.html', always_includes({
    'tasks': tasks,
    'stop':  stop,
    'start': start,
    'ranges': HUMAN_RANGES,
    'chosen_range': given_range,
    'filter_title': filter_title
  }, request, user))


@never_cache
def find_projects(request):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
    
  from tasks_data.misc import find_projects_by_name
  
  project_name = param('q', request.GET, '')
  projects = find_projects_by_name(user, project_name, 5)
  
  return render_to_response('tasks/matches.html', {
    'matches': projects,
    'query': project_name
  })
  
@never_cache
def find_contexts(request):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
  
  from tasks_data.misc import find_contexts_by_name
  
  context_name = param('q', request.GET, '')
  contexts = find_contexts_by_name(user, context_name, 5)
  contexts = map(lambda c: "@%s" % c, contexts)
  
  return render_to_response('tasks/matches.html', {
    'matches': contexts,
    'query': context_name
  })
  
@never_cache
def purge_list(request, task_list_name):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
  
  task_list = get_task_list(user, task_list_name)
  if not task_list:
    raise Http404
    
  from tasks_data.task_lists import archive_tasks
  from tasks_data.misc import create_undo
  
  undo = None
  if request.method == "POST":
    archived_tasks = archive_tasks(task_list, user)
    undo = create_undo(user, task_list=task_list, archived_tasks=archived_tasks)
  
  redirect = referer_redirect(user,request)
  
  if undo and undo.is_saved():
    from statusing import Statuses
    set_status_undo(redirect,Statuses.TASKS_PURGED,undo)
  
  return redirect

@never_cache
def delete_list(request, task_list_name):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
  
  task_list = get_task_list(user, task_list_name)
  if not task_list:
    raise Http404
  
  from tasks_data.task_lists import delete_task_list
  from tasks_data.misc import create_undo
  
  undo = None
  if len(get_task_lists(user)) > 1:
    deleted_tasks = delete_task_list(user, task_list)
    undo = create_undo(user, request=request, task_list=task_list, list_deleted=True, return_to_referer=True)
  
  redirect = default_list_redirect(user)
  
  if undo and undo.is_saved():
    from statusing import Statuses
    set_status_undo(redirect,Statuses.LIST_DELETED,undo)
  
  return redirect

@never_cache
def add_list(request):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
  
  from tasks_data.task_lists import add_task_list
  
  new_name = param('name', request.POST, '')
  new_list = None
  if request.method == "POST":
    if len(slugify(new_name)) > 0:
      new_list = add_task_list(user, new_name)
      return list_redirect(user, new_list)
      
  elif is_ajax(request): # GET
    return render_to_response('tasks/lists/add.html', {
      'user': user
    })
    
  return referer_redirect(user,request)

@never_cache
def undo(request, undo_id):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()

  from tasks_data.misc import do_undo
  from tasks_data.models import Undo
  from tasks_data.users import users_equal

  task_list = None
  try:
    undo = Undo.get_by_id(int(undo_id), parent=user)
      
    if undo:
      if not users_equal(undo.parent(), user):
        return access_error_redirect()
      do_undo(user, undo)
      task_list = undo.task_list
          
  except:
    import logging
    logging.exception("Error undoing!")
  
  if undo.return_uri:
    from django.http import HttpResponseRedirect
    return HttpResponseRedirect(undo.return_uri)
    
  else:
    return referer_redirect(user, request)

@never_cache
def task(request, task_id=None):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
  
  if task_id:
    task = Task.get_by_id(int(task_id), parent=user)
    if not task:
      raise Http404
  else:
    task = Task(parent=user, body='')
    
  from tasks_data.tasks import update_task_with_params, save_task
    
  force_complete   = param('force_complete', request.POST, None)
  force_uncomplete = param('force_uncomplete', request.POST, None)
  force_delete     = param('delete', request.GET, None)
  
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
      
    save_task(user, task)
    
  elif force_delete:
    from tasks_data.tasks import delete_task
    from tasks_data.misc import create_undo
    from tasks.statusing import get_status_message, Statuses
    status = get_status_message(Statuses.TASK_DELETED)
    delete_task(user,task)
    undo = create_undo(user, task_list=task.task_list, deleted_tasks=[task])
    
  elif request.method == "POST":
    update_task_with_params(user, task, request.POST)

    task_list = param('task_list',request.GET,None)
    if task_list:
      task.task_list = get_task_list(user, task_list)

    save_task(user, task)
  
  if undo:
    undo = undo.key().id()
  
  if not is_ajax(request):
    return referer_redirect(user, request)
    
  else:
    return render_to_response('tasks/tasks/ajax_task.html', {
      'user': user,
      'task': task,
      'status': status,
      'undo': undo
    })
    
@never_cache
def settings(request):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
    
  if request.method == "POST":
    from tasks_data.users import save_user
    
    user.hide_project  = param('show_project',  request.POST, None) is None
    user.hide_contexts = param('show_contexts', request.POST, None) is None
    user.hide_due_date = param('show_due_date', request.POST, None) is None
    
    save_user(user)
    
  elif is_ajax(request):
    return render_to_response('tasks/settings.html', {
      'user': user
    })

  return referer_redirect(user, request)

@never_cache
def transparent_settings(request):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
    
  if request.method == "POST":
    from tasks_data.users import save_user
    
    offset = param('offset', request.POST, None)
    try:
      user.timezone_offset_mins = int(offset)
      save_user(user)
      
    except:
      import logging
      logging.error("Couldn't update timezone offset to %s" % offset)
    
  if is_ajax(request):
    from django.http import HttpResponse
    return HttpResponse("OK")
  else:
    return referer_redirect(user, request)

@never_cache
def redirect(request, username=None):
  user = get_dnzo_user()
  if user:
    return most_recent_redirect(user)
  else:
    from django.core.urlresolvers import reverse as reverse_url
    from django.http import HttpResponseRedirect
    return HttpResponseRedirect(reverse_url('public.views.signup'))

#### UTILITY METHODS ####

def always_includes(params=None, request=None, user=None):
  if not params:
    params = {}
    
  if request:
    params['request_uri'] = request.get_full_path()
  if user:
    params['task_lists']  = get_task_lists(user)
    params['user']        = user
  
  import environment
  from google.appengine.api.users import create_logout_url
  
  params['is_production'] = environment.IS_PRODUCTION
  params['logout_url']    = create_logout_url('/')
  params['max_records']   = RESULT_LIMIT
  
  return params