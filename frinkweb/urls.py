from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	url(r'^(?P<timespan>(hourly|daily|weekly|all)?)/?$', 'stats.views.top_players'),
	url(r'^top_players/?(?P<timespan>(hourly|daily|weekly|all)?)/?$', 'stats.views.top_players'),
	url(r'^top_clans/?(?P<timespan>(hourly|daily|weekly|all)?)/?$', 'stats.views.top_clans'),
	url(r'^top_weapons/?(?P<timespan>(hourly|daily|weekly|all)?/?).*$', 'stats.views.top_weapons'),
	url(r'^player/(?P<player>[0-9a-zA-Z-_\.]+).png$', 'stats.views.banner'),
	url(r'^player/(?P<playername>[0-9a-zA-Z-_\.]+).json$', 'stats.views.player_json'),
 	url(r'^player/(?P<playername>[0-9a-zA-Z-_\.]+)/?(?P<timespan>(hourly|daily|weekly|all)?)/?(?P<kpage>\d*)/?(?P<dpage>\d*)/?$', 'stats.views.player_html'),
	url(r'^playersearch.*$', 'stats.views.player_search'),
	url(r'^clan/(?P<clanname>[\[\]\!0-9a-zA-Z-_]+)/?(?P<timespan>(hourly|daily|weekly|all)?)/?$', 'stats.views.clan'),
	url(r'^blacklist.*$','stats.views.blacklist'),
	url(r'^404.*$','stats.views.fourohfour'),
	url(r'^robots.txt.*$','stats.views.robots'),
	url(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/static/favicon.ico'}),
    # Example:
    # (r'^frinkweb/', include('frinkweb.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
