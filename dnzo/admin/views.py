from google.appengine.api.users import create_logout_url, get_current_user, is_current_user_admin

from django.shortcuts import render_to_response

from data.models import Invitation
from data.misc import get_invitation_by_address
from util.misc import param
  
def add_invitation(request):
  invitations = []
  
  if request.method == "POST":
    import re
    current_user = get_current_user()
    addresses = param('addresses', request.POST, '')
    addresses = re.split(r'\s+',addresses)
    
    for address in addresses:
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