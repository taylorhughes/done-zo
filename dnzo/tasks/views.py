from google.appengine.ext import db
from google.appengine.api.users import create_logout_url

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse as reverse_url

from tasks.models import *
from tasks.errors import *
from tasks.util import *

from datetime import datetime
from time import strptime
import logging


def always_includes(params=None):
  if not params:
    params = {}
  params['logout_url'] = create_logout_url('/')
  return params

def lists_index(request, username):
  try:
    user = verify_current_user(username)
  except AccessError:
    return access_error_redirect()
  
  new_list = TaskList(owner=user)
  new_list.editing = True
    
  if request.method == "POST":
    new_list.name = request.POST['name']
    new_list.short_name = urlize(new_list.name)
    new_list.put()
    
  lists = TaskList.gql('WHERE owner=:owner ORDER BY name ASC', owner=user).fetch(50)
  lists.insert(0, new_list)
  
  return render_to_response('task_lists/index.html', always_includes({
    'user': user,
    'task_lists': lists
  }))
  
def tasks_index(request, username, task_list=None, context_name=None, project_name=None):
  try:
    user = verify_current_user(username)
  except AccessError:
    return access_error_redirect()
  
  task_list = get_task_list(user, task_list)
  
  filter_title = None
  view_project = None
  if project_name:
    view_project = Project.gql('WHERE short_name=:1 AND owner=:2', project_name, user).get()
    if not view_project:
      raise Http404
    filter_title = view_project.name
  view_context = None
  if context_name:
    view_context = Context.gql('WHERE name=:1 AND owner=:2', context_name, user).get()
    if not view_context:
      raise Http404
    filter_title = "@%s" % view_context.name
      
  wheres = ['task_list=:task_list AND purged=:purged'] 
  params = { 'task_list': task_list, 'purged': False }
  add_url = reverse_url('tasks.views.task',args=[user.short_name,task_list.short_name])
  
  if view_context:
    wheres.append('contexts=:context')
    params['context'] = view_context.name
    add_url += "?context=%s" % view_context.name
  elif view_project:
    wheres.append('project=:project')
    params['project'] = view_project
    add_url += "?project=%s" % view_project.short_name

  sortable_columns = ('project', 'body', 'due_date', 'created_at', 'context')
  order, direction = 'created_at', 'ASC'
  if param('order', request.GET) in sortable_columns:
    order = param('order', request.GET)
  if param('descending', request.GET) == 'true':
    direction = 'DESC'
  
  gql = 'WHERE %s ORDER BY %s %s' % (' AND '.join(wheres), order, direction)
  
  tasks = Task.gql(gql, **params).fetch(50)
  
  return render_to_response('tasks/index.html', always_includes({
    'tasks': tasks,
    'user': user,
    'task_list': task_list,
    'filter_title': filter_title,
    'add_url': add_url,
    'order': order,
    'direction': direction,
    'request_uri': request.get_full_path()
  }))

def purge_tasks(request, username, task_list):
  try:
    user = verify_current_user(username)
  except AccessError:
    return access_error_redirect()
  
  task_list = get_task_list(user, task_list)
  
  if request.method == "POST":
    logging.info("Here")
    for task in Task.gql('WHERE task_list=:list AND purged=:purged AND complete=:complete', 
                         list=task_list, purged=False, complete=True).fetch(50):
      task.purged = True
      task.put()
  
  return HttpResponseRedirect(reverse_url('tasks.views.tasks_index', args=[username, task_list.short_name]))

def task(request, username, task_list=None, task_key=None):
  try:
    user = verify_current_user(username)
  except AccessError:
    return access_error_redirect()
  
  task_list = get_task_list(user, task_list)
  
  # We can't change the URL for the enclosing form element. Ugh.
  if not task_key and request.method == "POST":
    task_key = param('task_key',request.POST)
  
  if task_key:
    task = db.get(db.Key.from_path('Task', int(task_key)))
    #if task.owner != user:
    #  return access_error_redirect()
  else:
    task = Task(body='')
    task.owner = user
    
  force_complete = param('force_complete', request.POST, None)
  force_uncomplete = param('force_uncomplete', request.POST, None)
  
  if force_complete or force_uncomplete:
    if force_complete:
      task.complete = True
    else:
      task.complete = False
    task.put()
    
  elif request.method == "POST":
    task.complete = False
    if param('complete',request.POST) == "true":
      task.complete = True
    
    task.body = param('body',request.POST)
    
    raw_project = param('project',request.POST,'')
    if len(raw_project) > 0:
      raw_project_short = urlize(raw_project)
      project = Project.gql('WHERE owner=:user AND short_name=:name', 
                            user=user, name=raw_project_short).get()
      # Create the project if it doesn't exist
      if not project:
        project = Project(name=raw_project, short_name=raw_project_short, owner=user)
        project.put()
      task.project = project
    
    task.contexts = []
    raw_contexts = param('contexts',request.POST,'')
    raw_contexts = re.findall(r'[A-Za-z_-]+', raw_contexts)
    for raw_context in raw_contexts:
      raw_context = raw_context.lower()
      context = Context.gql('WHERE owner=:user AND name=:name', user=user, name=raw_context).get()
      if not context:
        context = Context(owner=user, name=raw_context)
        context.put()
      task.contexts.append(context.name)
    
    task.due_date = parse_date(param('due_date', request.POST))
    
    task.task_list = task_list
    task.put()
    
    if not is_ajax(request):
      # TODO: Return to referrer.
      return HttpResponseRedirect(
        reverse_url('tasks.views.tasks_index',args=[user.short_name,task_list.short_name])
      )
  
  elif request.method == "GET":
    raw_project = param('project', request.GET, None)
    if raw_project:
      task.project = Project.gql('WHERE owner=:user AND short_name=:project',
                                 user=user, project=raw_project).get()
    raw_context = param('context', request.GET, None)
    if raw_context:
      context = Context.gql('WHERE owner=:user AND name=:context',
                             user=user, context=raw_context).get()
      if context:
        task.contexts = [context.name]
        
    task.editing = True

  return render_to_response('tasks/task.html', {
    'task': task
  })

def redirect(request):
  user = get_dnzo_user()
  if user:
    return HttpResponseRedirect(reverse_url('tasks.views.lists_index',args=[user.short_name]))
  else:
    return HttpResponseRedirect('/')

def welcome(request):
  return render_to_response("index.html", {
    'user': get_dnzo_user()
  })

def signup(request):
  current_user = get_dnzo_user()
  if current_user:
    return HttpResponseRedirect('/tasks/')
  
  current_user = get_current_user()
  if not current_user:
    raise RuntimeException, "User must be logged in."

  if request.method == 'POST':
    short_name = request.POST['short_name']

    valid = True
    if not is_urlized(short_name):
      valid = False

    if valid:
      new_user = TasksUser(short_name = short_name, user = current_user)
      new_user.put()
      return HttpResponseRedirect('/tasks/')

  else:
    short_name = urlize(current_user.nickname())

  return render_to_response('signup/index.html', {
    'short_name': short_name
  })