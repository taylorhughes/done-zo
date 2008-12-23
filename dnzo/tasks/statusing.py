#
#  Some methods for passing status messages between views. 
#

class Statuses:
  TASKS_PURGED = 'archived'
  TASK_DELETED = 'deleted'
  LIST_DELETED = 'list_deleted'

def get_status_message(status):
  if status == Statuses.TASKS_PURGED:
    return "Completed tasks have been archived."
  if status == Statuses.TASK_DELETED:
    return "Task has been deleted."
  if status == Statuses.LIST_DELETED:
    return "List has been deleted."
    
  return None

COOKIE_STATUS = 'dnzo-status'
COOKIE_UNDO   = 'dnzo-undo'

def get_status_undo(request):
  from util.misc import param
  status = param(COOKIE_STATUS, request.COOKIES, None)
  
  try:
    from util.misc import param
    undo = int(param(COOKIE_UNDO, request.COOKIES, None))
  except:
    undo = None
  
  return (get_status_message(status), undo)

def reset_status_undo(response, status=None, undo=None):
  if status is not None:
    response.set_cookie(COOKIE_STATUS, '', max_age=-1)
  if undo is not None:
    response.set_cookie(COOKIE_UNDO, '', max_age=-1)
  
def set_status_undo(response, status=None, undo=None):
  if status is not None:
    response.set_cookie(COOKIE_STATUS, status, max_age=60)
  if undo is not None:
    response.set_cookie(COOKIE_UNDO, str(undo.key().id()), max_age=60)
