from django.conf.urls import url

from .views import (
    IndexSetDetailView, IndexSetListView, check_custom_index_list,
    custom_index_list_results)


urlpatterns = [
    url(r'^custom/$', check_custom_index_list, name='check_custom_index_list'),
    url(r'^custom/results/$', custom_index_list_results, name='custom_index_list_results'),
    url(r'^index_set/(?P<pk>\d+)/$', IndexSetDetailView.as_view(), name='index_set_detail'),
    url(r'^interactive/$', IndexSetListView.as_view(), name='index_set_list'),
]
