from google.appengine.ext import db

from tasks_data.models import Project, ProjectIndex, Context, Invitation, Undo

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
  
def find_projects_by_name(user, project_name, limit=5):
  from util.misc import indexize, zpad
  indexed_name = indexize(project_name)
  
  indexes = ProjectIndex.gql(
    "WHERE index >= :start AND index < :end AND ANCESTOR IS :user",
    start=indexed_name, end=zpad(indexed_name), user=user
  )
  
  return sorted_by_last_used(indexes, limit)
  
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
  
def find_contexts_by_name(user, context_name, limit=5):
  from util.misc import zpad, slugify
  indexed_name = slugify(context_name)
  
  contexts = Context.gql(
    "WHERE name >= :start AND name < :end AND ANCESTOR IS :user",
    start=indexed_name, end=zpad(indexed_name), user=user
  )
  
  return sorted_by_last_used(contexts, limit)

  
### UNDOS ###

def create_undo(user,
                request=None, 
                task_list=None,
                list_deleted=False, 
                deleted_tasks=None,
                archived_tasks=None,
                return_uri=None,
                return_to_referer=False):
                
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
  
  if return_uri is None and request and return_to_referer:
    from util.misc import get_referer
    return_uri = get_referer(request)
  undo.return_uri = return_uri

  undo.put()
  
  return undo
  

def do_undo(user, undo):
  for task in undo.find_deleted():
    from tasks_data.tasks import undelete_task
    undelete_task(task, undo.task_list)
    
  for task in undo.find_archived():
    task.archived = False
    task.put()
    
  if undo.list_deleted:
    from tasks_data.task_lists import undelete_task_list
    undelete_task_list(user, undo.task_list)
    
  undo.delete()

  
### MISC ###

def sorted_by_last_used(collection, limit):
  names_last_used = {}
  for index in collection:
    name, last_used_at = index.name, index.last_used_at
    if name not in names_last_used or last_used_at > names_last_used[name]:
      names_last_used[name] = last_used_at

  names = names_last_used.items()
  names.sort(key=lambda item: item[1])
  names.reverse()
  names = map(lambda item: item[0], names)

  return names[0:limit]
