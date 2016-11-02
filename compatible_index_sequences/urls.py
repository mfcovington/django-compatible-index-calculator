from django.conf.urls import url

from .views import (
    IndexSetDetailView, IndexSetListView, check_custom_index_list,
    custom_index_list_results)


urlpatterns = [
    url(r'^$', IndexSetListView.as_view(), name='index_set_list'),
    url(r'^index_set/(?P<pk>\d+)/$', IndexSetDetailView.as_view(), name='index_set_detail'),
    url(r'^check_list/$', check_custom_index_list, name='check_custom_index_list'),
    url(r'^check_list/results/$', custom_index_list_results, name='custom_index_list_results'),
]
