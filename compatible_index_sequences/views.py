import csv
import datetime
import itertools

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .classes import IndexingData
from .forms import (
    AutoIndexListForm, CompatibilityParameters, CustomIndexListForm,
    HiddenSampleSheetDownloadForm)
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
    return complete_index_set.objects.filter(sequence__iexact=index)


def auto(request):
    form = AutoIndexListForm(rows=10)
    if request.method == 'POST':
        form = AutoIndexListForm(request.POST, request.FILES, rows=10)
        if form.is_valid():
            config_distance = form.cleaned_data['config_distance']
            config_length = form.cleaned_data['config_length']
            indexing_data_set = form.cleaned_data['indexing_data_set']

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

            custom_list = indexing_data_set.get_index_1_sequences()
            index_list = generate_index_list_with_index_set_data(custom_list)

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
                min_distance=config_distance, previous_list=list(custom_list),
                timeout=timeout)

            if compatible_set:
                index_list.extend(
                    generate_index_list_with_index_set_data(compatible_set))
                indexing_data_set.add([IndexingData(seq) for seq in compatible_set])
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

            index_list_seqs = [index['sequence'] for index in index_list]
            hidden_download_form = HiddenSampleSheetDownloadForm(
                initial={
                    'index_list_csv': ','.join(index_list_seqs),
                    'sample_ids_csv': ','.join(indexing_data_set.get_sample_ids()),
                }
            )
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
            config_length_2 = form.cleaned_data['config_length_2']
            indexing_data_set = form.cleaned_data['indexing_data_set']

            custom_index_list = indexing_data_set.get_index_1_sequences()
            if dual_indexed:
                custom_index_list_2 = indexing_data_set.get_index_2_sequences()

                index_length_2 = minimum_index_length_from_lists(
                    custom_index_list_2, override_length=config_length_2)

            index_length = minimum_index_length_from_lists(
                custom_index_list, override_length=config_length)

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
                        pair[0][0:index_length_2].upper(),
                        pair[1][0:index_length_2].upper())
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
                    incompatible_index_pairs_2, length=index_length_2)
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

            index_list = generate_index_list_with_index_set_data(
                custom_index_list)
            index_list_seqs = [index['sequence'] for index in index_list]
            index_list_csv = ','.join(index_list_seqs)
            if dual_indexed:
                index_list_2 = generate_index_list_with_index_set_data(
                    custom_index_list_2)
                index_list_2_seqs = [index['sequence'] for index in index_list_2]
                index_list_2_csv = ','.join(index_list_2_seqs)
                index_list = list(zip(index_list, index_list_2))
            else:
                index_list_2_csv = []

            hidden_download_form = HiddenSampleSheetDownloadForm(
                initial={
                    'index_list_csv': index_list_csv,
                    'index_list_2_csv': index_list_2_csv,
                    'sample_ids_csv': ','.join(indexing_data_set.get_sample_ids()),
                    'dual_indexed': dual_indexed,
                }
            )

            context = {
                'dual_indexed': dual_indexed,
                'index_length': index_length,
                'index_list': index_list,
                'incompatible_indexes': [item for sublist in incompatible_alignments_seqs for item in sublist],
                'incompatible_index_pairs': zip(incompatible_alignments_seqs, incompatible_alignments),
                'hidden_download_form': hidden_download_form,
            }
            if dual_indexed:
                context['index_length_2'] = index_length_2
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
    ]

    if request.POST.get('dual_indexed') == "True":
        dual_indexed = True
    else:
        dual_indexed = False

    header_row = ['Sample_ID', 'Sample_Name', 'Sample_Plate', 'Sample_Well', 'I7_Index_ID', 'index']

    if dual_indexed:
        for row in data:
            row.extend(['', ''])
        header_row.extend(['I5_Index_ID', 'index2', 'Sample_Project', 'Description'])
        data.append(header_row)
    else:
        header_row.extend(['Sample_Project', 'Description'])
        data.append(header_row)

    sample_ids_csv = request.POST.get('sample_ids_csv')
    index_list_csv = request.POST.get('index_list_csv')
    index_list_2_csv = request.POST.get('index_list_2_csv')

    if dual_indexed:
        zipped_index_data = zip(
            sample_ids_csv.split(','),
            index_list_csv.split(','),
            index_list_2_csv.split(',')
        )
        for sample_id, index, index2 in zipped_index_data:
            hit_list = []
            hit2_list = []
            for hit in lookup_index_set(index):
                hit_list.append('{}:{}'.format(hit.index_set, hit.name))
            for hit2 in lookup_index_set(index2):
                hit2_list.append('{}:{}'.format(hit2.index_set, hit2.name))
            data.append(
                [sample_id, '', '', '', ', '.join(hit_list), index, ', '.join(hit2_list), index2, '', ''])
    else:
        zipped_index_data = zip(
            sample_ids_csv.split(','),
            index_list_csv.split(',')
        )
        for sample_id, index in zipped_index_data:
            hit_list = []
            for hit in lookup_index_set(index):
                hit_list.append('{}:{}'.format(hit.index_set, hit.name))
            data.append([sample_id, '', '', '', ', '.join(hit_list), index, '', ''])

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
        context['form'] = CompatibilityParameters()
        context['hidden_download_form'] = HiddenSampleSheetDownloadForm()
        return context
