from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^', include('public.urls')),
    (r'^', include('tasks.urls')),
    #(r'^admin/', include('admin.urls')),
)
