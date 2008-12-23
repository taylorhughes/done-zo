from django.conf.urls.defaults import patterns, include

urlpatterns = patterns('',
    (r'^admin/', include('admin.urls')),
    (r'^', include('public.urls')),
    (r'^', include('tasks.urls')),
)
