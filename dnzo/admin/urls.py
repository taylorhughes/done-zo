from django.conf.urls.defaults import *

urlpatterns = patterns('',
  (r'^add_invitation.html$', 'admin.views.add_invitation'),
  (r'^invitations.html$', 'admin.views.invitations'),
)