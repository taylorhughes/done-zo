from google.appengine.api.users import create_logout_url, get_current_user, is_current_user_admin

from django.shortcuts import render_to_response

from tasks_data.models import Invitation
from tasks_data.misc import get_invitation_by_address
from tasks_data.users import clear_user_memcache, save_user, get_dnzo_user
from util.misc import param
  
  
def migrate_user(request):
  from google.appengine.api.users import User
  
  error = None
  success = None
  if request.method == 'POST':
    dnzo_user = None
    dnzo_user_already = None
    google_user_to = None
    
    try:
      google_user_from = User(param('user_from', request.POST, None))
      dnzo_user = get_dnzo_user(invalidate_cache=True, google_user=google_user_from)
    
      google_user_to = User(param('user_to', request.POST, None))
      dnzo_user_already = get_dnzo_user(invalidate_cache=True, google_user=google_user_to)
      
    except:
      pass
    
    if dnzo_user is None:
      error = "Could not find existing DNZO user. Whoops!"
    elif dnzo_user_already is not None:
      error = "User exists already with that e-mail address! Delete him first."
    elif google_user_to is None:
      error = "Couldn't find the new Google user. Whoops!"
    else:
      clear_user_memcache(dnzo_user)
      dnzo_user.user = google_user_to
      save_user(dnzo_user)
      success = "Success! %s is now %s." % (google_user_from.email(), google_user_to.email())

  return render_to_response("admin/migrate_user.html", {
    'error': error,
    'success': success
  })
  
def add_invitation(request):
  invitations = []
  
  if request.method == "POST":
    import re
    current_user = get_current_user()
    addresses = param('addresses', request.POST, '')
    addresses = re.split(r'\s+',addresses)
    
    for address in addresses:
      address = address.lower()
      if not get_invitation_by_address(address):
        invitations.append(address)
        Invitation(
          email_address=address,
          added_by=current_user
        ).put()
  
  return render_to_response("admin/add_invitation.html", {
    'invitations': invitations
  })
  
def invitations(request):
  invitations = Invitation.gql('ORDER BY created_at DESC').fetch(100)
  return render_to_response("admin/invitations.html", {
    'invitations': invitations
  })
  
  
def migrations(request):
  from admin.migrations import MIGRATIONS
  
  return render_to_response("admin/migrations/index.html", {
    'migrations': MIGRATIONS
  })
  
def run_migration(request, migration_id):
  from admin.migrations import MIGRATIONS

  migration_index = 0
  try:
    migration_slugs = [migration['slug'] for migration in MIGRATIONS]
    migration_index = migration_slugs.index(migration_id)
  except:
    pass
    
  migration = MIGRATIONS[migration_index]

  if request.method == "POST":
    start = param('start', request.POST, None)
    
    total, updated, last_key = migration['migration'](start)

    return render_to_response("admin/migrations/migration_progress.html", {
      'migration': migration,
      'total':     total,
      'updated':   updated,
      'last_key':  last_key
    })
        
  else: 
    return render_to_response("admin/migrations/run_migration.html", {
      'migration': migration
    })
  
  
def settings(request):
  from django.http import HttpResponseRedirect
  from django.core.urlresolvers import reverse as reverse_url
  from tasks_data.runtime_settings import find_all, set_setting
  
  if request.method == "POST":
    name = param('setting', request.POST, None)
    value = param('value', request.POST, None)
    
    if name and value is not None:
      set_setting(name,value)
      return HttpResponseRedirect(reverse_url('admin.views.settings'))
  
  return render_to_response("admin/settings.html", {
    'settings': find_all()
  })
  
def counts(request):
  from tasks_data.counting import find_all_counts
  return render_to_response("admin/counts.html", {
    'counts': find_all_counts()
  })
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  