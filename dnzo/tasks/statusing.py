#
#  Some methods for passing status messages between views. 
#

class Statuses:
  TASKS_PURGED = 'archived'
  TASKS_NOT_PURGED = 'unarchived'
  TASK_DELETED = 'deleted'
  LIST_DELETED = 'list_deleted'

MESSAGES = {
  # NOTE: These are output in straight HTML with no encoding. 
  Statuses.TASKS_PURGED:     "Completed tasks have been archived.",
  Statuses.TASKS_NOT_PURGED: "No tasks to archive &mdash; complete some first!",
  Statuses.TASK_DELETED:     "Task has been deleted.",
  Statuses.LIST_DELETED:     "List has been deleted.",
}

def get_status_message(status):
  if status in MESSAGES:
    return MESSAGES[status]
    
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
