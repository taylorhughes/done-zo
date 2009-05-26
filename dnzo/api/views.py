
from tasks_data.users import get_dnzo_user

import environment

def json_response(*args,**kwargs):
  from django.utils import simplejson as json
  from django.http import HttpResponse
  
  response_body = json.dumps(kwargs)
  response = HttpResponse(response_body)
  if 'error' in kwargs:
    response.status_code = 400
    
  return response

def task(request,task_id=None):
  dnzo_user = get_dnzo_user()
  if not dnzo_user:
    return json_response(error="You must log in first.")
  
  from tasks_data.models import Task
  
  data = {}
  if request.method == 'GET':
    if task_id:
      # return individual task
      data['task'] = 'Individual task'
      
    else:
      # return all tasks
      data['tasks'] = map(lambda t: t.to_dict(), Task.all())
      
  elif request.method == 'POST':
    if task_id:
      # edit individual task
      data['task'] = 'Newly edited task'
      
    else:
      # add new task
      data['task'] = 'Newly added task'
  
  return json_response(**data)
  
def task_list(request):
  pass