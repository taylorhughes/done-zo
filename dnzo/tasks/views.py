from google.appengine.ext import db
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render_to_response

from tasks.models import *
from tasks.errors import *
from tasks.util import *

from datetime import datetime
from time import strptime
import logging

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
  
  return render_to_response('task_lists/index.html', {
    'user': user,
    'task_lists': lists
  })
  
  
def tasks_index(request, username, task_list=None, context_name=None, project_name=None):
  try:
    user = verify_current_user(username)
  except AccessError:
    return access_error_redirect()
  
  task_list = TaskList.gql('WHERE owner=:user AND short_name=:short_name', user=user, short_name=task_list).get()
  
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
  show_completed = 'show_completed' in request.GET and request.GET['show_completed'] == 'true'
  
  new_task = Task(body='')
  new_task.editing = True
  new_task.owner = user
  
  if request.method == "POST":
    body = request.POST['body']
    new_task.body = body    
    
    raw_project = request.POST['project'].strip()
    if len(raw_project) > 0:
      raw_project_short = urlize(raw_project)
      project = Project.gql('WHERE owner=:user AND short_name=:name', 
                            user=user, name=raw_project_short).get()
      if not project:
        project = Project(name=raw_project, short_name=raw_project_short, owner=user)
        project.put()
      new_task.project = project
    
    raw_contexts = request.POST['contexts']
    raw_contexts = re.findall(r'[A-Za-z_-]+', raw_contexts)
    for raw_context in raw_contexts:
      raw_context = raw_context.lower()
      context = Context.gql('WHERE owner=:user AND name=:name', user=user, name=raw_context).get()
      if not context:
        context = Context(owner=user, name=raw_context)
        context.put()
      new_task.contexts.append(context.name)
    
    if 'due_date' in request.POST:
      due_date = parse_date(request.POST['due_date'])
      new_task.due_date = due_date
      
    new_task.task_list = task_list
      
    new_task.put()

    if is_ajax(request):
      # return new task template
      pass

  wheres = ['task_list=:task_list'] 
  params = { 'task_list': task_list }
  
  if view_context:
    wheres.append('contexts=:context')
    params['context'] = view_context.name
  elif view_project:
    wheres.append('project=:project')
    params['project'] = view_project
  if not show_completed:
    wheres.append('complete=:complete')
    params['complete'] = False

  order = 'created_at DESC'

  gql = 'WHERE %s ORDER BY %s' % (' AND '.join(wheres), order)

  tasks = Task.gql(gql, **params).fetch(50)
  tasks.insert(0, new_task)
  
  return render_to_response('tasks/index.html', {
    'tasks': tasks,
    'user': user,
    'task_list': task_list,
    'filter_title': filter_title
  })

def task(request, username, task_key):
  try:
    user = verify_current_user(username)
  except AccessError:
    return access_error_redirect()

  task = Task.get(task_key)

  return render_to_response('tasks/task.html', {
    'task': task
  })

def redirect(request):
  user = get_dnzo_user()
  if user:
    return HttpResponseRedirect(user.tasks_url)
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