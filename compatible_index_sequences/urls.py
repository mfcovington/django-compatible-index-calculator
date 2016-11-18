from django.conf.urls import url

from .views import (
    IndexSetDetailView, InteractiveView, auto, custom,
    export_samplesheet, select_mode)


urlpatterns = [
    url(r'^$', select_mode, name='select_mode'),
    url(r'^auto/$', auto, name='auto'),
    url(r'^custom/$', custom, name='custom'),
    url(r'^export_samplesheet/$', export_samplesheet, name='export_samplesheet'),
    url(r'^index_set/(?P<pk>\d+)/$', IndexSetDetailView.as_view(), name='index_set_detail'),
    url(r'^interactive/$', InteractiveView.as_view(), name='interactive'),
]
