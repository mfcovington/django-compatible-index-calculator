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
    find_compatible_subset, find_incompatible_index_pairs,
    generate_incompatible_alignments, hamming_distance,
    index_list_from_samplesheet, is_self_compatible,
    minimum_index_length_from_lists, minimum_index_length_from_sets,
    optimize_set_order)


def generate_index_list_with_index_set_data(index_list):
    index_list_with_data = []
    for sequence in index_list:
        index_set_data = lookup_index_set(sequence)
        index_list_with_data.append(
            {'sequence': sequence, 'index_set_data': index_set_data})
    return index_list_with_data


def lookup_index_set(index, complete_index_set=Index):
    return complete_index_set.objects.filter(sequence=index)


def auto(request):
    form = AutoIndexListForm(rows=10)
    if request.method == 'POST':
        form = AutoIndexListForm(request.POST, request.FILES, rows=10)
        if form.is_valid():
            config_distance = form.cleaned_data['config_distance']
            config_length = form.cleaned_data['config_length']

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

            users_index_list = form.cleaned_data['index_list'].splitlines()
            users_index_list.extend(index_list_from_samplesheet(request))
            index_list = generate_index_list_with_index_set_data(users_index_list)
            order = optimize_set_order(*index_set_list)

            try:
                custom_list = [i['sequence'] for i in index_list]
            except:
                custom_list = []

            index = {'set': [], 'size': []}
            for o in order:
                index['set'].append(index_set_list[o])
                index['size'].append(subset_size_list[o])

            if config_length is None:
                min_length = min(
                    minimum_index_length_from_lists(custom_list),
                    minimum_index_length_from_sets(index['set'])
                )
            else:
                min_length = config_length

            if not is_self_compatible(custom_list, config_distance, min_length):
                incompatible_index_pairs = find_incompatible_index_pairs(
                    custom_list, min_distance=config_distance,
                    index_length=min_length)
                incompatible_alignments = generate_incompatible_alignments(
                    incompatible_index_pairs, length=min_length)
                index_list = generate_index_list_with_index_set_data(custom_list)

                context = {
                    'index_list': index_list,
                    'incompatible_indexes':
                        [item for sublist in incompatible_index_pairs for item in sublist],
                    'incompatible_index_pairs':
                        zip(incompatible_index_pairs, incompatible_alignments),
                }
                return render(
                    request, 'compatible_index_sequences/custom_results.html', context)

            if form.cleaned_data['extend_search_time']:
                timeout = 60
            else:
                timeout = 10

            compatible_set = find_compatible_subset(
                index['set'], index['size'], min_length=min_length,
                min_distance=config_distance, previous_list=custom_list,
                timeout=timeout)

            if compatible_set:
                index_list.extend(
                    generate_index_list_with_index_set_data(compatible_set))
            else:
                index_list = []
                print('WARNING: NO COMPATIBLE SETS FOUND')

            if find_compatible_subset.timed_out:
                context = {
                    'form': form,
                    'timed_out': True,
                }
                print('WARNING: TIMED OUT')
                return render(
                    request, 'compatible_index_sequences/auto.html', context)

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
        form = CustomIndexListForm(request.POST, request.FILES)
        if form.is_valid():
            config_distance = form.cleaned_data['config_distance']
            dual_indexed = form.cleaned_data['dual_indexed']
            config_length = form.cleaned_data['config_length']
            custom_index_list = form.cleaned_data['index_list']

            if dual_indexed:
                (custom_index_list, custom_index_list_2) = zip(
                    *[pair.split(',') for pair in custom_index_list])

            if config_length is None:
                index_length = minimum_index_length_from_lists(custom_index_list)
            else:
                index_length = config_length

            incompat_seqs_1, incompat_poss_1 = find_incompatible_index_pairs(
                custom_index_list, min_distance=config_distance,
                index_length=index_length, sequences=True,
                positions=True)

            if dual_indexed:
                subset_seq_2 = {
                    e: [custom_index_list_2[i] for i in p]
                    for e, p in enumerate(incompat_poss_1)
                }

                both_incompatible = []
                for i, pair in subset_seq_2.items():
                    distance = hamming_distance(
                        pair[0][0:index_length].upper(),
                        pair[1][0:index_length].upper())
                    if distance < config_distance:
                        both_incompatible.append(i)

                incompatible_index_pairs = []
                incompatible_index_pairs_2 = []
                for i in both_incompatible:
                    incompatible_index_pairs.append(incompat_seqs_1[i])
                    incompatible_index_pairs_2.append(subset_seq_2[i])

            else:
                incompatible_index_pairs = incompat_seqs_1

            incompatible_alignments = generate_incompatible_alignments(
                incompatible_index_pairs, length=index_length)

            incompatible_alignments_seqs = []

            if dual_indexed:
                incompatible_alignments_2 = generate_incompatible_alignments(
                    incompatible_index_pairs_2, length=index_length)
                incompatible_alignments = [
                    '{} + {}'.format(a[0], a[1]) for a in zip(
                        incompatible_alignments, incompatible_alignments_2)]
                zipped_pairs = zip(
                    incompatible_index_pairs, incompatible_index_pairs_2)
                for pair_1, pair_2 in zipped_pairs:
                    incompatible_alignments_seqs.append(
                        ['{}   {}'.format(i[0], i[1])
                            for i in zip(pair_1, pair_2)])
            else:
                incompatible_alignments_seqs = incompatible_index_pairs

            index_list = generate_index_list_with_index_set_data(custom_index_list)

            hidden_download_form = HiddenSampleSheetDownloadForm(
                initial={'index_list_csv': ','.join([index['sequence'] for index in index_list])})
            context = {
                'index_list': index_list,
                'incompatible_indexes': [item for sublist in incompatible_index_pairs for item in sublist],
                'incompatible_index_pairs': zip(incompatible_alignments_seqs, incompatible_alignments),
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
