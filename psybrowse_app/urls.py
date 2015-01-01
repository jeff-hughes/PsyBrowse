from django.conf.urls import patterns, url

from psybrowse_app import views

urlpatterns = patterns('',
    url(r'^$', views.index,
        name='index'),  # ex: /psybrowse/

    url(r'^recent_articles/?$', views.recent_articles,
        name='recent articles default'),  # ex: /psybrowse/recent_articles/
    url(r'^recent_articles/(?P<num_articles>\d+)/?$', views.recent_articles,
        name='recent articles'),  # ex: /psybrowse/recent_articles/100/

    # VIEW DETAIL:
    url(r'^article/(?P<article_id>\d+)/?$', views.article_detail,
        name='article detail'),  # ex: /psybrowse/article/5/
    url(r'^author/(?P<author_id>\d+)/?$', views.author_detail,
        name='author detail'),  # ex: /psybrowse/author/7/
    url(r'^journal/(?P<journal_id>\d+)/?$', views.journal_detail,
        name='journal detail'),  # ex: /psybrowse/journal/28/
    url(r'^keyword/(?P<keyword_id>\d+)/?$', views.keyword_detail,
        name='keyword detail'),  # ex: /psybrowse/keyword/42/
    url(r'^user/(?P<user_id>\d+)/?$', views.user_detail,
        name='user detail'),  # ex: /psybrowse/user/42/

    # SEARCH:
    url(r'^search/?$', views.search,
        name='search'),  # ex: /psybrowse/search/
    url(r'^adv_search/?$', views.adv_search,
        name='advanced search'),  # ex: /psybrowse/adv_search/

    # USER PAGES:
    url(r'^register/?$', views.register,
        name='register'),  # ex: /psybrowse/register/
    url(r'^login/?$', 'django.contrib.auth.views.login',
        {
            'template_name': 'psybrowse_app/login.html',
            'extra_context': {'next':'/'}
        },
        name='login'),  # ex: /psybrowse/login/
    url(r'^logout/?$', views.logout_page,
        name='logout'),  # ex: /psybrowse/logout/

    # SUBSCRIBE:
    url(r'^subscribe/?$', views.subscribe,
        name='subscribe'),  # ex: /psybrowse/subscribe/?type=article&id=21
    url(r'^unsubscribe/?$', views.unsubscribe,
        name='unsubscribe'),  # ex: /psybrowse/unsubscribe/?type=article&id=21
    url(r'^unsubscribe_all/?$', views.unsubscribe_all,
        name='unsubscribe all'),  # ex: /psybrowse/unsubscribe_all/
    url(r'^subscriptions/?$', views.subscriptions,
        name='subscriptions'),  # ex: /psybrowse/subscriptions/
)