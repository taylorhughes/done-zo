from django.http import Http404
from django.shortcuts import render_to_response
from django.views.decorators.cache import never_cache

from tasks.data      import *
from tasks.models    import Task
from tasks.redirects import default_list_redirect, list_redirect, access_error_redirect, referer_redirect
from util.misc       import param, is_ajax, urlize
from tasks.statusing import *

SORTABLE_LIST_COLUMNS = ('complete', 'project_index', 'body', 'due_date', 'created_at', 'context')

#### VIEWS ####

@never_cache
def list_index(request, task_list_name=None, context_name=None, project_index=None):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
  
  task_list = get_task_list(user, task_list_name)
  if not task_list or task_list.deleted:
    raise Http404
  
  # FILTER 
  filter_title = None
  view_project = None
  view_project_name = None
  if project_index:
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

  wheres = ['task_list=:task_list AND archived=:archived'] 
  params = { 'task_list': task_list, 'archived': False }

  if view_context:
    wheres.append('contexts=:context')
    params['context'] = view_context
  elif view_project:
    wheres.append('project_index=:project_index')
    params['project_index'] = view_project

  default_order, default_direction = 'created_at', 'ASC'
  
  if param('order', request.GET) in SORTABLE_LIST_COLUMNS:
    order = param('order', request.GET)
    direction = 'ASC'
    if param('descending', request.GET) == 'true':
      direction = 'DESC'
    
    order_by = '%s %s, %s %s' % (order, direction, default_order, default_direction)
  
  else:
    order, direction = default_order, default_direction
    order_by = '%s %s' % (order, direction)
  
  gql = 'WHERE %s ORDER BY %s' % (' AND '.join(wheres), order_by)
  tasks = Task.gql(gql, **params).fetch(50)
  
  # SHOW STATUS MESSAGE AND UNDO
  status = get_status(request)
  undo = get_undo(request)
  
  new_task_attrs = {'body': '', 'parent': user}
  if view_context:
    new_task_attrs['contexts'] = [view_context]
  if view_project:
    new_task_attrs['project'] = view_project_name
  
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
    'new_tasks': [new_task]
  }, request, user))
  
  reset_status(response,status)
  reset_undo(response,undo)
  
  return response

@never_cache
def archived_index(request, task_list_name=None, context_name=None, project_index=None):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
    
  wheres = ['ANCESTOR IS :user AND archived=:archived AND deleted=:deleted'] 
  params = { 'user': user, 'archived': True, 'deleted': False }

  from datetime import datetime, timedelta
  stop  = datetime.utcnow()
  start = datetime.utcnow() - timedelta(days=7)
  filter_title = "This week"
  
  wheres.append('completed_at >= :start AND completed_at < :stop')
  params['stop']  = stop
  params['start'] = start

  gql = 'WHERE %s ORDER BY completed_at DESC' % ' AND '.join(wheres)
  tasks = Task.gql(gql, **params)
    
  return render_to_response('tasks/archived.html', always_includes({
    'tasks': tasks,
    'stop':  stop,
    'start': start,
    'filter_title': filter_title
  }, request, user))


@never_cache
def find_projects(request):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
  
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
  
  undo = None
  if request.method == "POST":
    undo = Undo(task_list=task_list, parent=user)
    for task in get_completed_tasks(task_list):
      task.archived = True
      task.put()
      undo.archived_tasks.append(task.key())
    undo.put()
  
  redirect = referer_redirect(user,request)
  
  if undo and undo.is_saved():
    set_status(redirect,Statuses.TASKS_PURGED)
    set_undo(redirect,undo)
  
  return redirect

@never_cache
def delete_list(request, task_list_name):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
  
  task_list = get_task_list(user, task_list_name)
  if not task_list:
    raise Http404
  
  undo = None
  if request.method == "POST" and len(get_task_lists(user)) > 1:
    undo = delete_task_list(task_list)
  
  redirect = default_list_redirect(user)
  
  if undo and undo.is_saved():
    set_status(redirect,Statuses.LIST_DELETED)
    set_undo(redirect,undo)
  
  return redirect

@never_cache
def add_list(request):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
  
  new_name = param('name', request.POST, '')
  new_list = None
  if request.method == "POST":
    if len(urlize(new_name)) > 0:
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

  task_list = None
  try:
    undo = Undo.get_by_id(int(undo_id), parent=user)
      
    if undo:
      if not users_equal(undo.parent(), user):
        return access_error_redirect()
      do_undo(undo)
      task_list = undo.task_list
      
  except RuntimeError, (errno, strerror):
    logger.error("Error undoing: " + strerror)
  
  if task_list:
    return list_redirect(user, task_list)
    
  else:
    return referer_redirect(user, request)

@never_cache
def task(request, task_id=None):
  user = get_dnzo_user()
  if not user:
    return access_error_redirect()
  
  task_list = param('task_list',request.GET,None)
  if task_list:
    task_list = get_task_list(user, task_list)
  
  # We can't change the URL for the enclosing form element. Ugh.
  if not task_id and request.method == "POST":
    task_id = param('task_id',request.POST)
  
  if task_id:
    task = Task.get_by_id(int(task_id), parent=user)
    if not task:
      raise Http404
  else:
    task = Task(parent=user, body='')
    
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
      
    task.put()
    
  elif force_delete:
    status = get_status_message(Statuses.TASK_DELETED)
    undo = delete_task(task)
    
  elif request.method == "POST":
    update_task_with_params(user, task, request.POST)
    task.task_list = task_list
    save_task(task)
  
  
  if undo:
    undo = undo.key().id()
  
  if not is_ajax(request):
    # TODO: Something useful.
    return default_list_redirect(user)
    
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
    user.hide_project  = param('show_project',  request.POST, None) is None
    user.hide_contexts = param('show_contexts', request.POST, None) is None
    user.hide_due_date = param('show_due_date', request.POST, None) is None
    user.put()
    
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
    offset = param('offset', request.POST, None)
    try:
      user.timezone_offset_mins = int(offset)
      user.put()
    except:
      import logging
      logging.error("Couldn't update offset to %s" % offset)
    
  if is_ajax(request):
    from django.http import HttpResponse
    return HttpResponse("OK")
  else:
    return referer_redirect(user, request)

@never_cache
def redirect(request, username=None):
  user = get_dnzo_user()
  if user:
    return default_list_redirect(user)
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
  
  return params