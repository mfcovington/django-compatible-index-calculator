from django.conf.urls import url

from .views import IndexSetListView


urlpatterns = [
    url(r'^$', IndexSetListView.as_view(), name='index_set_list')
]
