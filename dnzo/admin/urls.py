from admin.views import AddInvitationHandler, InvitationsHandler, ModifyUserHandler, \
  MigrateUserHandler, DeleteUserHandler, SettingsHandler, CountsHandler, MigrationsHandler, \
  RunMigrationHandler

ADMIN_URLS = (
  (r'/admin/add_invitation.html', AddInvitationHandler),
  (r'/admin/invitations.html', InvitationsHandler),
  (r'/admin/modify_user.html', ModifyUserHandler),
  (r'/admin/migrate_user.html', MigrateUserHandler),
  (r'/admin/delete_user.html', DeleteUserHandler),
  (r'/admin/settings.html', SettingsHandler),
  (r'/admin/counts.html', CountsHandler),

  (r'/admin/migrations.html', MigrationsHandler),
  (r'/admin/run_migration/<:[a-z_-]+>', RunMigrationHandler),
)