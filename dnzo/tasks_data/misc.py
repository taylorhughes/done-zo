from google.appengine.ext import db

from tasks_data.models import Project, Context, Invitation, Undo

# Max projects to store in the datastore for autocomplete
MAX_PROJECTS = 50
MAX_CONTEXTS = 50

### Invitations ###

def get_invitation_by_address(address):
  address = address.lower()
  return Invitation.gql("WHERE email_address=:address", address=address).get()

### PROJECTS ###

def get_project(user, project_name):
  return Project.get_by_key_name(
             Project.name_to_key_name(project_name),
             parent=user
         )

def save_project(user, project_name):
  project = get_project(user, project_name)
  
  if not project:
    project = create_project(user, project_name)
    
  plist = user.mru_projects or []
  if project_name in plist:
    plist.remove(project_name)
  plist.insert(0,project_name)
  user.mru_projects = plist[:MAX_PROJECTS]
  
  return project
  
def create_project(user, project_name):
  from util.misc import slugify
  short_name = slugify(project_name)
  key_name = Project.name_to_key_name(project_name)
  project = Project(
    parent=user, 
    key_name=key_name,
    name=project_name, 
    short_name=short_name
  )
  project.put()

  return project
  
def get_project_by_short_name(user, short_name):
  project = Project.gql(
    'WHERE ANCESTOR IS :user AND short_name=:short_name ' + 
    'ORDER BY created_at DESC',
    user=user, short_name=short_name
  ).get()
  
  if project:
    return project.name
  return None
  
  
### CONTEXTS ###

def get_context(user, context_name):
  return Context.get_by_key_name(
    Context.name_to_key_name(context_name),
    parent=user
  )

def save_contexts(user, contexts):
  for context in contexts:
    save_context(user, context)
  
def save_context(user, context_name):
  context = get_context(user,context_name)
  if not context:
    context = Context(
      parent=user,
      name=context_name,
      key_name=Context.name_to_key_name(context_name)
    )
    context.put()
    
  plist = user.mru_contexts or []
  if context_name in plist:
    plist.remove(context_name)
  plist.insert(0,context_name)
  user.mru_contexts = plist[:MAX_CONTEXTS]
    
  return context

  
### UNDOS ###

def create_undo(user,
                request=None, 
                task_list=None,
                list_deleted=False, 
                deleted_tasks=None,
                archived_tasks=None,
                return_uri=None):
                
  undo = Undo(parent=user)
  
  if deleted_tasks and len(deleted_tasks) > 0:
    for task in deleted_tasks:
      undo.deleted_tasks.append(task.key())

  if archived_tasks and len(archived_tasks) > 0:
    for task in archived_tasks:
      undo.archived_tasks.append(task.key())

  if task_list:
    undo.task_list = task_list
    undo.list_deleted = list_deleted
  
  undo.return_uri = return_uri

  undo.put()
  
  return undo
  

def do_undo(user, undo):
  for task in undo.find_deleted():
    from tasks_data.tasks import undelete_task
    undelete_task(task, undo.task_list)
    
  if undo.list_deleted:
    from tasks_data.task_lists import undelete_task_list
    undelete_task_list(user, undo.task_list)
  
  archived = undo.find_archived()
  if len(archived) > 0:
    from tasks_data.task_lists import unarchive_tasks
    unarchive_tasks(undo.task_list, archived)
    
  undo.delete()