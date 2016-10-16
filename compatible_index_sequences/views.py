from django.shortcuts import render
from django.views.generic import ListView

from .models import IndexSet


class IndexSetListView(ListView):

    model = IndexSet
    template_name = 'compatible_index_sequences/index_set_list_view.html'
