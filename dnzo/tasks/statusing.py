#
#  Some methods for passing status messages between views. 
#

from util.misc import param

class Statuses:
  TASKS_PURGED = 'purged'
  TASK_DELETED = 'deleted'
  LIST_DELETED = 'list_deleted'

def get_status_message(status):
  if status == Statuses.TASKS_PURGED:
    return "Completed tasks have been archived"
  if status == Statuses.TASK_DELETED:
    return "Task has been deleted"
  if status == Statuses.LIST_DELETED:
    return "List has been deleted"
    
  return None

COOKIE_STATUS = 'dnzo-status'
COOKIE_UNDO   = 'dnzo-undo'

def get_status(request):
  status = param(COOKIE_STATUS, request.COOKIES, None)
  return get_status_message(status)
  
def set_status(response, status):
  response.set_cookie(COOKIE_STATUS, status, max_age=60)
  
def reset_status(response, status):
  if status:
    response.set_cookie(COOKIE_STATUS, '', max_age=-1)
  
def get_undo(request):
  try:
    undo = int(param(COOKIE_UNDO, request.COOKIES, None))
  except:
    undo = None
  return undo
  
def set_undo(response, undo):
  response.set_cookie(COOKIE_UNDO, str(undo.key().id()), max_age=60)
  
def reset_undo(response,undo):
  if undo:
    response.set_cookie(COOKIE_UNDO, '', max_age=-1)