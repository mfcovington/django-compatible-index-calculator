from django.conf.urls import url

from .views import (
    IndexSetDetailView, InteractiveView, check_custom_index_list,
    custom_index_list_results, select_mode)


urlpatterns = [
    url(r'^$', select_mode, name='select_mode'),
    url(r'^custom/$', check_custom_index_list, name='check_custom_index_list'),
    url(r'^custom/results/$', custom_index_list_results, name='custom_index_list_results'),
    url(r'^index_set/(?P<pk>\d+)/$', IndexSetDetailView.as_view(), name='index_set_detail'),
    url(r'^interactive/$', InteractiveView.as_view(), name='interactive'),
]
