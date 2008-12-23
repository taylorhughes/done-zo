from data.models import Project, ProjectIndex, Context, Invitation

### Invitations ###

def get_invitation_by_address(address):
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
    
  else:
    for index in project.indexes:
      # TODO: update in a transaction?
      from datetime import datetime
      index.last_used_at = datetime.utcnow()
      index.put()
    
  return project
  
def create_project(user, project_name):
  def txn(user, project):
    from util.misc import indexize
    import re
    
    project.put()
    name = indexize(project.name)[0:MAX_INDEX_LENGTH]
    tokens = re.split(r'\s+', name)
    for i in range(0,len(tokens)):
      token = ' '.join(tokens[i:])
      index = ProjectIndex(parent=user, index=token, name=project.name, project=project)
      index.put()
    
  
  from util.misc import urlize
  short_name = urlize(project_name)
  key_name = Project.name_to_key_name(project_name)
  project = Project(
    parent=user, 
    key_name=key_name,
    name=project_name, 
    short_name=short_name
  )
    
  db.run_in_transaction(txn, user, project)

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
    
  from datetime import datetime
  context.last_used_at = datetime.utcnow()
  context.put()
  
def find_contexts_by_name(user, context_name, limit=5):
  from util.misc import urlize, zpad
  indexed_name = urlize(context_name)
  
  contexts = Context.gql(
    "WHERE name >= :start AND name < :end AND ANCESTOR IS :user",
    start=indexed_name, end=zpad(indexed_name), user=user
  )
  
  return sorted_by_last_used(contexts, limit)

  
### UNDOS ###

def do_undo(user, undo):
  for task in undo.find_deleted():
    undelete_task(task, undo.task_list)
    
  for task in undo.find_archived():
    task.archived = False
    task.put()
    
  if undo.list_deleted:
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
