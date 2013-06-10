# -*- coding: utf-8 -*- 

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
  Statuses.TASKS_NOT_PURGED: "No tasks to archive — complete some first!",
  Statuses.TASK_DELETED:     "Task has been deleted.",
  Statuses.LIST_DELETED:     "List has been deleted.",
}

def get_status_message(status):
  if status in MESSAGES:
    return MESSAGES[status]
    
  return None
