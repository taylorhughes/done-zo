from django.conf.urls.defaults import patterns, include

urlpatterns = patterns('',
    (r'^admin/', include('admin.urls')),
    (r'^', include('public.urls')),
    (r'^', include('tasks.urls')),
)

handler404 = 'public.views.handler404'
handler500 = 'public.views.handler500'