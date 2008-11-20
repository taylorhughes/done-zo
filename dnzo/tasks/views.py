from google.appengine.api.users import create_logout_url

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse as reverse_url
from django.views.decorators.cache import never_cache

from tasks.models    import *
from tasks.errors    import *
from tasks.data      import *
from tasks.redirects import *
from tasks.statusing import *
from util.misc       import *
from util.parsing    import parse_date

import environment
import logging

ARCHIVED_LIST_NAME = '_archived'

SORTABLE_LIST_COLUMNS = ('project_index', 'body', 'due_date', 'created_at', 'context')

#### VIEWS ####

@never_cache
def list_index(request, username, task_list_name=None, context_name=None, project_index=None):
  try:
    user = verify_current_user(username)
  except AccessError:
    return access_error_redirect()
    
  archived = (task_list_name == ARCHIVED_LIST_NAME)
  if not archived:
    task_list = get_task_list(user, task_list_name)
    if not task_list or task_list.deleted:
      return default_list_redirect(user)
  else:
    task_list = None
      
  # FILTER 
  filter_title = None
  view_project = None
  view_project_name = None
  if project_index:
    view_project_name = get_project_by_index(user, project_index)
    if view_project_name:
      filter_title = view_project_name
      view_project = project_index
    else:
      return default_list_redirect(user)
      
  view_context = None
  if context_name:
    view_context = context_name
    filter_title = "@%s" % context_name

  if not archived:
    template = 'tasks/index.html'
    wheres = ['task_list=:task_list AND archived=:archived'] 
    params = { 'task_list': task_list, 'archived': False }
  else:
    template = 'tasks/archived.html'
    wheres = ['ANCESTOR IS :user AND archived=:archived AND deleted=:deleted'] 
    params = { 'user': user, 'archived': True, 'deleted': False }

  add_url = reverse_url('tasks.views.task',args=[user.short_name])
  if view_context:
    wheres.append('contexts=:context')
    params['context'] = view_context
    add_url += "?context=%s" % view_context
  elif view_project:
    wheres.append('project_index=:project_index')
    params['project_index'] = view_project
    add_url += "?project=%s" % view_project

  order, direction = 'created_at', 'ASC'
  if param('order', request.GET) in SORTABLE_LIST_COLUMNS:
    order = param('order', request.GET)
  if param('descending', request.GET) == 'true':
    direction = 'DESC'
  
  gql = 'WHERE %s ORDER BY %s %s' % (' AND '.join(wheres), order, direction)
  tasks = Task.gql(gql, **params).fetch(50)
  
  # SHOW STATUS MESSAGE AND UNDO
  status = get_status(request)
  undo = get_undo(request)
  
  new_task_attrs = {'body': ''}
  if view_context:
    new_task_attrs['context'] = [view_context]
  if view_project:
    new_task_attrs['project'] = view_project_name
  
  new_task = Task(**new_task_attrs)
  new_task.editing = True
    
  response = render_to_response(template, always_includes({
    'tasks': tasks,
    'task_list': task_list,
    'filter_title': filter_title,
    'add_url': add_url,
    'order': order,
    'direction': direction,
    'status': status,
    'undo': undo,
    'archived': archived,
    'new_tasks': [new_task]
  }, request, user))
  
  reset_status(response,status)
  reset_undo(response,undo)
  
  return response

@never_cache
def purge_list(request, username, task_list_name):
  try:
    user = verify_current_user(username)
  except AccessError:
    return access_error_redirect()
  
  task_list = get_task_list(user, task_list_name)
  if not task_list or not users_equal(task_list.parent(), user):
    return access_error_redirect()
  
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
def delete_list(request, username, task_list_name):
  try:
    user = verify_current_user(username)
  except AccessError:
    return access_error_redirect()
  
  task_list = get_task_list(user, task_list_name)
  if not task_list or not users_equal(task_list.parent(), user):
    return access_error_redirect()
  
  undo = None
  if request.method == "POST" and len(get_task_lists(user)) > 1:
    undo = delete_task_list(task_list)
  
  redirect = default_list_redirect(user)
  
  if undo and undo.is_saved():
    set_status(redirect,Statuses.LIST_DELETED)
    set_undo(redirect,undo)
  
  return redirect

@never_cache
def add_list(request, username):
  try:
    user = verify_current_user(username)
  except AccessError:
    return access_error_redirect()
  
  new_name = param('name', request.POST, '')
  new_list = None
  if request.method == "POST":
    if len(urlize(new_name)) > 0:
      new_list = add_task_list(user, new_name)
      return list_redirect(user, new_list)
      
    else:
      return referer_redirect(user,request)
      
  else: # GET
    return render_to_response('tasks/lists/index.html', {
      'user': user
    })

@never_cache
def undo(request, username, undo_id):
  try:
    user = verify_current_user(username)
  except AccessError:
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
def task(request, username, task_id=None):
  try:
    user = verify_current_user(username)
  except AccessError:
    return access_error_redirect()
  
  task_list = param('task_list',request.GET,None)
  if task_list:
    task_list = get_task_list(user, task_list)
  
  # We can't change the URL for the enclosing form element. Ugh.
  if not task_id and request.method == "POST":
    task_id = param('task_id',request.POST)
  
  if task_id:
    task = Task.get_by_id(int(task_id), parent=user)
    if not task or not users_equal(task.parent(), user):
      return access_error_redirect()
  else:
    task = Task(parent=user, body='')
    
  force_complete   = param('force_complete', request.POST, None)
  force_uncomplete = param('force_uncomplete', request.POST, None)
  force_delete     = param('delete', request.GET, None)
  
  status = None
  undo = None
  
  if force_complete or force_uncomplete or force_delete:
    if force_complete or force_uncomplete:
      task.complete = (not force_uncomplete)
      task.put()
      
    elif force_delete:
      status = "Task deleted successfully."
      undo = delete_task(task)
    
  elif request.method == "POST":
    task.complete = False
    if param('complete',request.POST) == "true":
      task.complete = True
    
    task.body = param('body',request.POST)
    
    task.project = None
    raw_project = param('project',request.POST,'').strip()
    if len(raw_project) > 0:
      task.project       = raw_project
      task.project_index = urlize(raw_project)
    
    task.contexts = []
    raw_contexts = param('contexts',request.POST,'')
    raw_contexts = re.findall(r'[A-Za-z_-]+', raw_contexts)
    for raw_context in raw_contexts:
      task.contexts.append(urlize(raw_context))
    
    task.due_date = parse_date(param('due_date', request.POST))
    task.task_list = task_list

    save_task(task)
    
  elif request.method == "GET":
    raw_project = param('project', request.GET, None)
    if raw_project:
      task.project = raw_project
      
    raw_context = param('context', request.GET, None)
    if raw_context:
      task.contexts = [raw_context]
        
    task.editing = True
  
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
def redirect(request, username=None):
  user = get_dnzo_user()
  logging.info("user is %s" % user)
  if user:
    return default_list_redirect(user)
  else:
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
    
  params['logout_url'] = create_logout_url('/')
  
  return params