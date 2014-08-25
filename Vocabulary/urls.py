from django.conf.urls import patterns, url
from Vocabulary import views

## All URLs begin with /words/
urlpatterns = patterns('',
    url(r'^$', views.LexiconView.as_view(), name="lexicon"),
    url(r'^(?P<pk>\d+)/$', views.WordView.as_view(), name="detail"),
    url(r'^list/$', views.WordlistView.as_view(), name="wordlist"),
    url(r'^lookup/(\w+)/$', views.LookupView.as_view(), name="lookup"),
)