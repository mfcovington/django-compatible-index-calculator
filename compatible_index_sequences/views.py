import csv
import datetime
import itertools

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .forms import (
    AutoIndexListForm, CustomIndexListForm, HiddenSampleSheetDownloadForm)
from .models import Index, IndexSet
from .utils import (
    find_incompatible_index_pairs, generate_alignment, index_list_from_samplesheet,
    lookup_index_set)


def auto(request):
    form = AutoIndexListForm()
    if request.method == 'POST':
        form = AutoIndexListForm(request.POST)
        if form.is_valid():
            index_set_1 = form.cleaned_data['index_set_1']
            subset_size_1 = form.cleaned_data['subset_size_1']
            auto_set_1 = index_set_1.index_set.all()[0:subset_size_1]

            index_set_2 = form.cleaned_data['index_set_2']
            subset_size_2 = form.cleaned_data['subset_size_2']
            try:
                auto_set_2 = index_set_2.index_set.all()[0:subset_size_2]
            except:
                auto_set_2 = []

            index_set_3 = form.cleaned_data['index_set_3']
            subset_size_3 = form.cleaned_data['subset_size_3']
            try:
                auto_set_3 = index_set_3.index_set.all()[0:subset_size_3]
            except:
                auto_set_3 = []

            index_list = []

            for sequence in index_list_from_samplesheet(request):
                index_set_data = lookup_index_set(sequence)
                index_list.append(
                    {'sequence': sequence, 'index_set_data': index_set_data})

            for index in itertools.chain(auto_set_1, auto_set_2, auto_set_3):
                sequence = index.sequence
                index_set_data = lookup_index_set(sequence)
                index_list.append(
                    {'sequence': sequence, 'index_set_data': index_set_data})

            hidden_download_form = HiddenSampleSheetDownloadForm(
                initial={'index_list_csv': ','.join([index['sequence'] for index in index_list])})
            context = {
                'hidden_download_form': hidden_download_form,
                'index_list': index_list,
            }
            return render(request, 'compatible_index_sequences/auto_results.html', context)
        else:
            print("INVALID INPUT")

    return render(request, 'compatible_index_sequences/auto.html', {'form': form})


def custom(request):
    form = CustomIndexListForm()
    if request.method == 'POST':
        form = CustomIndexListForm(request.POST)
        if form.is_valid():
            custom_index_list = form.cleaned_data['index_list'].splitlines()
            custom_index_list.extend(index_list_from_samplesheet(request))

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

            hidden_download_form = HiddenSampleSheetDownloadForm(
                initial={'index_list_csv': ','.join([index['sequence'] for index in index_list])})
            context = {
                'index_list': index_list,
                'incompatible_indexes': [item for sublist in incompatible_index_pairs for item in sublist],
                'incompatible_index_pairs': zip(incompatible_index_pairs, incompatible_alignments),
                'hidden_download_form': hidden_download_form,
            }
            return render(request, 'compatible_index_sequences/custom_results.html', context)
        else:
            print("INVALID INPUT")

    return render(
        request, 'compatible_index_sequences/custom.html', {'form': form})


def export_samplesheet(request):

    data = [
        ['[Header]', '', '', '', '', '', '', ''],
        ['IEMFileVersion', '4', '', '', '', '', '', ''],
        ['InvestigatorName', '', '', '', '', '', '', ''],
        ['ExperimentName', '', '', '', '', '', '', ''],
        ['Date', '', '', '', '', '', '', ''],
        ['Workflow', '', '', '', '', '', '', ''],
        ['Application', '', '', '', '', '', '', ''],
        ['Assay', '', '', '', '', '', '', ''],
        ['Description', '', '', '', '', '', '', ''],
        ['Chemistry', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['[Reads]', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['[Settings]', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['[Data]', '', '', '', '', '', '', ''],
        ['Sample_ID', 'Sample_Name', 'Sample_Plate', 'Sample_Well', 'I7_Index_ID', 'index', 'Sample_Project', 'Description'],
    ]
    index_list_csv = request.POST.get('index_list_csv')
    for index in index_list_csv.split(','):
        data.append(['', '', '', '', '', index, '', ''])

    filename = request.POST.get('filename')
    if filename == '':
        filename = 'SampleSheet.{:%Y%m%d.%H%M%S}.csv'.format(datetime.datetime.now())
    response = HttpResponse(content_type='text/csv')
    response[
        'Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    writer = csv.writer(response)
    writer.writerows(data)

    return response


def select_mode(request):
    return render(request, 'compatible_index_sequences/select_mode.html')


class IndexSetDetailView(DetailView):

    model = IndexSet
    template_name = 'compatible_index_sequences/index_set_detail_view.html'


class InteractiveView(ListView):

    model = IndexSet
    template_name = 'compatible_index_sequences/interactive.html'

    def get_context_data(self, **kwargs):
        context = super(InteractiveView, self).get_context_data(**kwargs)
        context['hidden_download_form'] = HiddenSampleSheetDownloadForm()
        return context
