import csv
import datetime
import itertools
import time

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .forms import (
    AutoIndexListForm, CustomIndexListForm, HiddenSampleSheetDownloadForm)
from .models import Index, IndexSet
from .utils import (
    find_incompatible_index_pairs, generate_alignment, index_list_from_samplesheet,
    join_two_compatible_sets, is_self_compatible, minimum_index_length,
    optimize_set_order, remove_incompatible_indexes_from_queryset)


def is_timed_out(start_time, timeout):
    return time.time() - start_time > timeout


def lookup_index_set(index, complete_index_set=Index):
    return complete_index_set.objects.filter(sequence=index)


def auto(request):
    form = AutoIndexListForm()
    if request.method == 'POST':
        form = AutoIndexListForm(request.POST)
        if form.is_valid():
            index_set_list = [
                form.cleaned_data['index_set_1'],
                form.cleaned_data['index_set_2'],
                form.cleaned_data['index_set_3']
            ]
            subset_size_list = [
                form.cleaned_data['subset_size_1'],
                form.cleaned_data['subset_size_2'],
                form.cleaned_data['subset_size_3']
            ]

            order = optimize_set_order(*index_set_list)
            index = {'set': [], 'size': []}
            for o in order:
                index['set'].append(index_set_list[o])
                index['size'].append(subset_size_list[o])

            min_length_0 = index['set'][0].min_length()

            try:
                min_length_1 = index['set'][1].min_length()
            except:
                min_length_1 = float('inf')
                is_selected_1 = False
            else:
                is_selected_1 = True

            try:
                min_length_2 = index['set'][2].min_length()
            except:
                min_length_2 = float('inf')
                is_selected_2 = False
            else:
                is_selected_2 = True

            min_length = min(min_length_0, min_length_1, min_length_2)

            start_time = time.time()
            timed_out = False
            if form.cleaned_data['extend_search_time']:
                timeout = 60
            else:
                timeout = 10

            compatible_set = None
            is_self_compatible_0 = index['set'][0].is_self_compatible(length=min_length)
            for auto_set_0 in itertools.combinations(index['set'][0].index_set.all(), index['size'][0]):
                auto_set_1 = []
                auto_set_2 = []

                index_list_0 = [i.sequence for i in auto_set_0]
                if not is_self_compatible_0:
                    if not is_self_compatible(index_list_0, length=min_length):
                        if is_timed_out(start_time, timeout):
                            timed_out = True
                            break
                        next
                    else:
                        compatible_set = index_list_0
                else:
                    compatible_set = index_list_0

                if is_selected_1:
                    compatible_set = None
                    index_set_1_trunc = remove_incompatible_indexes_from_queryset(
                        index['set'][1], index_list_0, length=min_length)

                    is_self_compatible_1 = is_self_compatible(
                        [i.sequence for i in index_set_1_trunc], length=min_length)

                    if len(index_set_1_trunc) > index['size'][1]:
                        next

                    for auto_set_1 in itertools.combinations(index_set_1_trunc, index['size'][1]):
                        auto_set_2 = []

                        index_list_1 = [i.sequence for i in auto_set_1]
                        index_list_01 = join_two_compatible_sets(
                            index_list_0, index_list_1, is_self_compatible_1, min_length)
                        compatible_set = index_list_01

                        if not compatible_set:
                            if is_timed_out(start_time, timeout):
                                timed_out = True
                                break
                            next
                        else:
                            if is_selected_2:
                                compatible_set = None
                                index_set_2_trunc = remove_incompatible_indexes_from_queryset(
                                    index['set'][2], index_list_01, length=min_length)

                                is_self_compatible_2 = is_self_compatible(
                                    [i.sequence for i in index_set_2_trunc], length=min_length)

                                if len(index_set_2_trunc) > index['size'][2]:
                                    next

                                for auto_set_2 in itertools.combinations(index_set_2_trunc, index['size'][2]):
                                    index_list_2 = [i.sequence for i in auto_set_2]
                                    compatible_set = join_two_compatible_sets(
                                        index_list_01, index_list_2, is_self_compatible_2, min_length)

                                    if not compatible_set:
                                        if is_timed_out(start_time, timeout):
                                            timed_out = True
                                            break
                                        next
                                    else:
                                        break
                            break

                if compatible_set:
                    break

            if not compatible_set:
                print('WARNING: NO COMPATIBLE SETS FOUND')

            if timed_out:
                context = {
                    'form': form,
                    'timed_out': True,
                }
                return render(request, 'compatible_index_sequences/auto.html', context)

            index_list = []

            for sequence in index_list_from_samplesheet(request):
                index_set_data = lookup_index_set(sequence)
                index_list.append(
                    {'sequence': sequence, 'index_set_data': index_set_data})

            for index in itertools.chain(auto_set_0, auto_set_1, auto_set_2):
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
