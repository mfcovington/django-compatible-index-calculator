from django.shortcuts import render
from django.views.generic import ListView

from .forms import CustomIndexListForm
from .models import Index, IndexSet


def check_custom_index_list(request):
    form = CustomIndexListForm()
    if request.method == 'POST':
        form = CustomIndexListForm(request.POST)
        if form.is_valid():
            print("CUSTOM INDEX LIST:\n{}".format(form.cleaned_data['index_list']))
        else:
            print("INVALID INPUT")
    context = {
        'index_list': Index.objects.all(),
        'form': form,
    }
    return render(
        request, 'compatible_index_sequences/check_custom_index_list.html', context)


class IndexSetListView(ListView):

    model = IndexSet
    template_name = 'compatible_index_sequences/index_set_list_view.html'
