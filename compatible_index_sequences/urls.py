from django.conf.urls import url

from .views import IndexSetListView, check_custom_index_list


urlpatterns = [
    url(r'^$', IndexSetListView.as_view(), name='index_set_list'),
    url(r'^check_list/$', check_custom_index_list, name='check_custom_index_list'),
]
