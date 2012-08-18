from django.conf.urls import patterns, include, url

urlpatterns = patterns('folivora.views',
    url('^$', 'folivora_index', name='folivora_index'),
    url('^projects/$', 'project_list', name='folivora_project_list'),
    url('^projects/add$', 'project_add', name='folivora_project_add'),
    url('^project/(?P<slug>[\w-]+)/$', 'project_detail', name='folivora_project_detail'),
)
