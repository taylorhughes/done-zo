from django.conf.urls.defaults import *

urlpatterns = patterns('',
  (r'^$', 'public.views.welcome'),
  (r'^signup/$', 'public.views.signup'),
  (r'^signup/availability/$', 'public.views.availability'),
  (r'^signup/closed.html$', 'public.views.closed'),
)