from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .forms import CustomIndexListForm
from .models import Index, IndexSet
from .utils import (
    find_incompatible_index_pairs, generate_alignment, lookup_index_set)


def custom(request):
    form = CustomIndexListForm()
    if request.method == 'POST':
        form = CustomIndexListForm(request.POST)
        if form.is_valid():
            custom_index_list = form.cleaned_data['index_list'].splitlines()

            incompatible_index_pairs = find_incompatible_index_pairs(
                custom_index_list)

            incompatible_alignments = []
            for pair in incompatible_index_pairs:
                incompatible_alignments.append(generate_alignment(*pair))

            index_list = []
            for sequence in custom_index_list:
                index_set_data = lookup_index_set(sequence)
                index_list.append(
                    {'sequence': sequence, 'index_set_data': index_set_data})

            context = {
                'index_list': index_list,
                'incompatible_indexes': [item for sublist in incompatible_index_pairs for item in sublist],
                'incompatible_index_pairs': zip(incompatible_index_pairs, incompatible_alignments),
            }
            return render(request, 'compatible_index_sequences/custom_results.html', context)
        else:
            print("INVALID INPUT")

    return render(
        request, 'compatible_index_sequences/custom.html', {'form': form})


def custom_results(request):
    return render(
        request, 'compatible_index_sequences/custom_results.html')


def select_mode(request):
    return render(request, 'compatible_index_sequences/select_mode.html')


class IndexSetDetailView(DetailView):

    model = IndexSet
    template_name = 'compatible_index_sequences/index_set_detail_view.html'


class InteractiveView(ListView):

    model = IndexSet
    template_name = 'compatible_index_sequences/interactive.html'
