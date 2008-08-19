from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^', include('tasks.urls')),
    #(r'^admin/', include('admin.urls')),
)
