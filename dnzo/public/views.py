
from google.appengine.api.users import create_logout_url, create_login_url, get_current_user, is_current_user_admin

from application_handler import DNZORequestHandler

import environment
import logging

class WelcomeHandler(DNZORequestHandler):
  def get(self):
    if self.dnzo_user:
      self.most_recent_redirect()
      return
    
    nickname = None
    current_user = get_current_user()
    if current_user:
      nickname = current_user.nickname()
  
    return self.render("public/index.html",
      nickname=nickname,
      logout_url=create_logout_url('/'),
      login_url=create_login_url(self.url_for('RedirectHandler')),
      is_development=environment.IS_DEVELOPMENT
    )

class SignupHandler(DNZORequestHandler):
  def get(self):  
    if self.dnzo_user:
      self.most_recent_redirect()
      return
    
    from tasks_data.misc import get_invitation_by_address
    from tasks_data.users import create_user
    from tasks_data.runtime_settings import get_setting
    
    current_user = get_current_user()
    allowed      = False
    invitation   = None
  
    if get_setting('registration_open'):
      allowed = True
    elif is_current_user_admin():
      allowed = True
    else:
      invitation = get_invitation_by_address(current_user.email())
      allowed = invitation is not None
  
    if not allowed:
      self.redirect(self.url_for('ClosedHandler'))
      return

    from tasks_data.models import TasksUser
    from tasks_data.tasks import DEFAULT_TASKS
    from tasks_data.task_lists import DEFAULT_LIST_NAME
  
    self.dnzo_user = create_user(current_user, DEFAULT_LIST_NAME, DEFAULT_TASKS)
  
    if invitation:
      from datetime import datetime
      invitation.registered_at = datetime.now()
      invitation.put()
      
    self.default_list_redirect()

class ClosedHandler(DNZORequestHandler):
  def get(self):
    nickname = None
    current_user = get_current_user()
    if current_user:
      nickname = current_user.nickname()
  
    self.render("public/signup/closed.html",
      nickname=nickname,
      logout_url=create_logout_url('/'),
      is_development=environment.IS_DEVELOPMENT
    )
  
  
