from google.appengine.ext import db
from google.appengine.api.users import create_logout_url

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse as reverse_url

from tasks.models    import *
from tasks.errors    import *
from tasks.data      import *
from tasks.statusing import *
from util.misc       import *
from util.parsing    import parse_date

import environment
import logging

DEFAULT_LIST_NAME = 'Tasks'
ARCHIVED_LIST_NAME = '_archived'

SORTABLE_LIST_COLUMNS = ('project_index', 'body', 'due_date', 'created_at', 'context')

MINIMUM_USER_URL_LENGTH = 5

#### VIEWS ####

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
  if project_index:
    project_name = get_project_by_index(user, project_index)
    if project_name:
      filter_title = project_name
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
    template = 'archived_tasks/index.html'
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
  }, request, user))
  
  reset_status(response,status)
  reset_undo(response,undo)
  
  return response

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
      
      return HttpResponseRedirect(
        reverse_url('tasks.views.list_index', args=[user.short_name,new_list.short_name])
      )
    else:
      return referer_redirect(user,request)
      
  else: # GET
    return render_to_response('lists/index.html', {
      'user': user
    })

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
    return HttpResponseRedirect(
             reverse_url('tasks.views.list_index', 
                         args=[user.short_name,task_list.short_name])
           )
  else:
    return referer_redirect(user,request)
  
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
    return render_to_response('tasks/ajax_task.html', {
      'user': user,
      'task': task,
      'status': status,
      'undo': undo
    })
    
def redirect(request, username=None):
  user = get_dnzo_user()
  logging.info("user is %s" % user)
  if user:
    return default_list_redirect(user)
  else:
    return HttpResponseRedirect(reverse_url('tasks.views.signup'))

def welcome(request):
  return render_to_response("index.html", {
    'user': get_dnzo_user()
  })

def availability(request):
  name = param('name', request.GET, '')
  message = username_invalid(name)
  
  if is_ajax(request):
    return render_to_response('signup/availability_ajax.html', {
      'unavailable': message is not None,
      'message':     message
    })
  else:
    return HttpResponseRedirect(reverse_url('tasks.views.signup'))

def signup(request):
  current_user = get_dnzo_user()
  if current_user:
    return default_list_redirect(current_user)
  
  current_user = get_current_user()

  if request.method == 'POST':
    name = param('name',request.POST)
    message = username_invalid(name)

    if not message:
      new_user = TasksUser(
        key_name=TasksUser.name_to_key_name(name), 
        user=current_user,
        short_name = name
      )
      new_user.put()
      
      # Create a default new list for this user
      tasks_list = add_task_list(new_user, DEFAULT_LIST_NAME)
      
      return default_list_redirect(new_user)

  else:
    message = None
    original = urlize(current_user.nickname())
    i, name = 1, original
    while not username_available(name):
      name = "%s_%s" % (original, i)
      i += 1

  return render_to_response('signup/index.html', {
    'short_name':  name,
    'unavailable': message is not None,
    'message':     message
  })

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
  
def username_invalid(new_name):
  message = None
    
  if not is_urlized(new_name):
    message = 'URLs can only contain lowercase letters, numbers, underscores and hyphens.'
    urlized = urlize(new_name)
    if len(urlized) >= MINIMUM_USER_URL_LENGTH:
      message += " How about &ldquo;%s&rdquo;?" % urlized
    
  elif not len(new_name) >= MINIMUM_USER_URL_LENGTH:
    message = 'URLs must be at least %s characters long.' % MINIMUM_USER_URL_LENGTH
    
  elif not username_available(new_name):
    message = 'Unfortunately, that URL has been taken.'
    
  return message
  