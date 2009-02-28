from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
  (r'^add_invitation.html$', 'admin.views.add_invitation'),
  (r'^invitations.html$', 'admin.views.invitations'),
  (r'^modify_user.html$', 'admin.views.modify_user'),
  (r'^migrate_user.html$', 'admin.views.migrate_user'),
  (r'^delete_user.html$', 'admin.views.delete_user'),
  (r'^settings.html$', 'admin.views.settings'),
  (r'^counts.html$', 'admin.views.counts'),

  (r'^migrations.html$', 'admin.views.migrations'),
  (r'^run_migration/(?P<migration_id>[a-z_-]+)$', 'admin.views.run_migration'),
)