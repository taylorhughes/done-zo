from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^admin/', include('admin.urls')),
    (r'^', include('public.urls')),
    (r'^', include('tasks.urls')),
)
