
from public.models   import *

def get_invitation_by_address(address):
  return Invitation.gql("WHERE email_address=:address", address=address).get()
  
  