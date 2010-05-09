from google.appengine.api.users import create_logout_url, get_current_user, is_current_user_admin

from tasks_data.models import Invitation
from tasks_data.misc import get_invitation_by_address
from tasks_data.users import clear_user_memcache, save_user, get_dnzo_user, get_dnzo_user_by_email

from dnzo_request_handler import DNZORequestHandler

class AddInvitationHandler(DNZORequestHandler):
  def get(self):
    self.render("admin/add_invitation.html", invitations=[])

  def post(self):
    import re
    invitations = []
  
    current_user = get_current_user()
    addresses = self.request.get('addresses', '')
    addresses = re.split(r'\s+',addresses)
  
    for address in addresses:
      address = address.lower()
      if not get_invitation_by_address(address):
        invitations.append(address)
        Invitation(
          email_address=address,
          added_by=current_user
        ).put()
  
    self.render("admin/add_invitation.html", invitations=invitations)
  
class InvitationsHandler(DNZORequestHandler):
  def get(self):
    invitations = Invitation.gql('ORDER BY created_at DESC').fetch(100)
    self.render("admin/invitations.html", invitations=invitations)
    
class ModifyUserHandler(DNZORequestHandler):
  def get(self):
    self.render("admin/modify_user.html")
    
class MigrateUserHandler(DNZORequestHandler):
  def get(self):
    self.redirect_to('ModifyUserHandler')
  def post(self):
    from google.appengine.api.users import User
  
    error = None
    success = None
    dnzo_user = None
    dnzo_user_already = None
    google_user_to = None
  
    try:
      from_email = self.request.get('user_from', None)
      dnzo_user = get_dnzo_user_by_email(from_email)
  
      google_user_to = User(self.request.get('user_to', None))
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
      success = "Success! %s is now %s." % (from_email, google_user_to.email())

    self.render("admin/modify_user.html", error=error, success=success)
  
class DeleteUserHandler(DNZORequestHandler):
  def get(self):
    self.redirect_to('ModifyUserHandler')
  def post(self):
    from google.appengine.api.users import User
  
    error = None
    success = None
    from_email = self.request.get('user', None)
    dnzo_user = get_dnzo_user_by_email(from_email)
    
    if dnzo_user is None:
      error = "Could not find existing user."
    else:
      from tasks_data.users import delete_user_and_data
      
      try:
        delete_user_and_data(dnzo_user)
        success = "User %s deleted!" % from_email
        
      except:
        import sys
        import logging
        logging.exception("Exception occurred while deleting a user")
        error = "Exception occurred while saving: %s" % sys.exc_info()[0]
    
    self.render("admin/modify_user.html", error=error, success=success)

class SettingsHandler(DNZORequestHandler):
  def get(self):
    from tasks_data.runtime_settings import find_all
    self.render("admin/settings.html", settings=find_all())
    
  def post(self):
    from tasks_data.runtime_settings import set_setting

    name = self.request.get('setting', None)
    value = self.request.get('value', None)
  
    if name and value is not None:
      set_setting(name,value)

    self.redirect_to('SettingsHandler')
    
class CountsHandler(DNZORequestHandler):
  def get(self):
    from tasks_data.counting import find_all_counts
    self.render("admin/counts.html", counts=find_all_counts())
    
class MigrationsHandler(DNZORequestHandler):
  def get(self):
    from admin.migrations import MIGRATIONS
    self.render("admin/migrations/index.html", migrations=MIGRATIONS)
    
class RunMigrationHandler(DNZORequestHandler):
  def post(self, migration_id):
    self.get(migration_id, is_post=True)
    
  def get(self, migration_id, is_post=False):
    from admin.migrations import MIGRATIONS

    migration_index = 0
    try:
      migration_slugs = [migration['slug'] for migration in MIGRATIONS]
      migration_index = migration_slugs.index(migration_id)
    except:
      pass
    
    migration = MIGRATIONS[migration_index]

    if is_post:
      start = self.request.get('start', None)
    
      total, updated, last_key = migration['migration'](start)

      self.render("admin/migrations/migration_progress.html",
        migration=migration,
        total=total,
        updated=updated,
        last_key=last_key
      )
        
    else: 
      self.render("admin/migrations/run_migration.html", migration=migration)
  
  
  
  
  