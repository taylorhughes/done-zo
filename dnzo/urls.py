from django.conf.urls.defaults import patterns, include, handler404, handler500

urlpatterns = patterns('',
    (r'^admin/', include('admin.urls')),
    (r'^', include('public.urls')),
    (r'^', include('tasks.urls')),
    (r'^api/0.1/', include('api.urls')),
)