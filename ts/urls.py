from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from dajaxice.core import dajaxice_autodiscover, dajaxice_config


admin.autodiscover()
dajaxice_autodiscover()

# administration password reset urls
urlpatterns = patterns('',
    url(r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset', name='admin_password_reset'),
    url(r'^admin/password_reset/done/$', 'django.contrib.auth.views.password_reset_done', name='password_reset_done'),
    url(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', name='password_reset_confirm'),
    url(r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete', name='password_reset_complete'),
    url(r'^admin/templatesadmin/', include('templatesadmin.urls')),
)

# administration apps
urlpatterns += patterns('',
    url(r'^rosetta/', include('rosetta.urls')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

# tinyMCE editor
urlpatterns += patterns('',
    url(r'^tinymce/', include('tinymce.urls')),
)

# dajaxice urls
urlpatterns += patterns('',
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
)

# flat pages
urlpatterns += patterns('django.contrib.flatpages.views',
    (r'^page/(?P<url>[0-9A-Za-z]+)/$', 'flatpage'),
)

# static files url patterns
urlpatterns += staticfiles_urlpatterns()

# serve static files from media directory when in debug mode
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.MEDIA_ROOT, }),
   )

# tradeschool app urls
urlpatterns += patterns('',
    url(r'^u/sdb/', 'tradeschool.views.switch_default_branch', name='switch-default-branch'),
    url(r'^start-a-tradeschool/', 'tradeschool.views.start_a_tradeschool', name='start-a-tradeschool'),
    url(r'^story/', 'tradeschool.views.story', name='story'),
    url(r'^school-submitted/(?P<slug>[0-9A-Za-z\-_]+)', 'tradeschool.views.branch_submitted', name='branch-submitted'),
    url(r'^cluster/(?P<slug>[0-9A-Za-z\-_]+)/', 'tradeschool.views.cluster_list', name='cluster-list'),
    url(r'^(?P<branch_slug>[0-9A-Za-z\-_]+)/', include('tradeschool.urls')),
    url(r'^$', 'tradeschool.views.branch_list', name='branch-list'),
)
