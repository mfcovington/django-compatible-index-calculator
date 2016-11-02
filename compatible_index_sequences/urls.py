from django.conf.urls import url

from .views import (
    IndexSetDetailView, InteractiveView, custom,
    custom_results, select_mode)


urlpatterns = [
    url(r'^$', select_mode, name='select_mode'),
    url(r'^custom/$', custom, name='custom'),
    url(r'^custom/results/$', custom_results, name='custom_results'),
    url(r'^index_set/(?P<pk>\d+)/$', IndexSetDetailView.as_view(), name='index_set_detail'),
    url(r'^interactive/$', InteractiveView.as_view(), name='interactive'),
]
