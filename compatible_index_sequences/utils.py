import codecs
import csv
import itertools
import re
import time
from collections import deque, OrderedDict

from .classes import IndexingData, IndexingDataSet


def find_compatible_subset(index_set_list, subset_size_list, min_length,
                           min_distance=3, previous_list=[], timeout=10,
                           start_time=None):

    find_compatible_subset.timed_out = False

    if start_time is None:
        start_time = time.time()
    compatible_subset = []

    index_set_list = deque(index_set_list)
    subset_size_list = deque(subset_size_list)

    try:
        index_set = index_set_list.popleft()
        current_list = [i.sequence for i in index_set.index_set.all()]
    except:
        return None

    index_list = remove_incompatible_indexes_from_queryset(
        current_list, previous_list, length=min_length)
    subset_size = subset_size_list.popleft()

    if len(index_list) < subset_size:
        return []

    self_compatible_list = is_self_compatible(index_list, min_distance,
                                              min_length)

    for index_subset in itertools.combinations(index_list, subset_size):

        if not self_compatible_list:
            if not is_self_compatible(index_subset, min_distance, min_length):
                if is_timed_out(start_time, timeout=timeout):
                    find_compatible_subset.timed_out = True
                    return []
                continue
            else:
                compatible_subset = list(index_subset)
        else:
            compatible_subset = list(index_subset)

        if len(index_set_list) > 0:
            previous_list.extend(compatible_subset)
            new_list = find_compatible_subset(
                index_set_list, subset_size_list, min_length, min_distance,
                previous_list, timeout, start_time)
            if new_list:
                compatible_subset.extend(new_list)
            elif new_list is not None:
                compatible_subset = []

        if compatible_subset:
            break

    return compatible_subset


def find_incompatible_index_pairs(index_list, min_distance=3,
                                  index_length=None, sequences=True,
                                  positions=False):
    if index_length is None:
        index_length = minimum_index_length_from_lists(index_list)

    incompatible_pairs = []
    incompatible_positions = []
    for pair in itertools.combinations(enumerate(index_list), 2):
        distance = hamming_distance(
            pair[0][1][0:index_length].upper(),
            pair[1][1][0:index_length].upper())
        if distance < min_distance:
            incompatible_pairs.append((pair[0][1], pair[1][1]))
            incompatible_positions.append((pair[0][0], pair[1][0]))

    if sequences and positions:
        return (incompatible_pairs, incompatible_positions)
    elif sequences:
        return incompatible_pairs
    elif positions:
        return incompatible_positions
    else:
        raise ValueError('Sequences and/or positions must be set to True.')


def generate_alignment(this, that, mark_unaligned=True, length=float('inf')):
    alignment = ''.join(
        ['|' if a == b else ' ' for a, b in zip(this.upper(), that.upper())])

    if mark_unaligned:
        len_diff = abs(len(this) - len(that))
        alignment += '-' * len_diff

    if len(alignment) > length:
        alignment = alignment[0:length] + '-' * (len(alignment) - length)

    return alignment


def generate_incompatible_alignments(incompatible_index_pairs,
                                     length=None):
    if length is None:
        length = float('inf')

    incompatible_alignments = []
    for pair in incompatible_index_pairs:
        incompatible_alignments.append(
            generate_alignment(*pair, length=length))
    return incompatible_alignments


def hamming_distance(this, that):
    if not this or not that or len(this) != len(that):
        return None
    elif this == that:
        return 0
    else:
        return sum(1 for a, b in zip(this, that) if a != b)


def index_list_from_samplesheet(request=None, files=None):
    if request is None and files is None:
        raise ValueError('Need either a request object or files.')
    elif files is None:
        file_list = [
            request.FILES.get('samplesheet_1'),
            request.FILES.get('samplesheet_2')
        ]
    elif request is None:
        file_list = [
            files.get('samplesheet_1'),
            files.get('samplesheet_2')
        ]
    else:
        raise ValueError('Need either a request object or files, not both.')

    indexing_data_set = IndexingDataSet()
    dual_indexed = False

    for file in file_list:
        if file is None:
            continue
        reader = csv.reader(codecs.iterdecode(file, 'utf-8'))
        header_done = False
        for row in reader:
            if header_done:
                index_1 = row[index1_column].replace(' ', '')
                is_valid_sequence(index_1)
                indexing_data = IndexingData(index_1,
                    index_1_id = row[index1_id_column].split(','),
                    sample_id=row[sample_id_column])
                if dual_indexed:
                    index_2 = row[index2_column].replace(' ', '')
                    is_valid_sequence(index_2)
                    indexing_data.index_2_sequence = index_2
                    indexing_data.index_2_id = row[index2_id_column].split(',')
                indexing_data_set.add(indexing_data)
            if 'Sample_ID' in row:
                header_done = True
                sample_id_column = row.index('Sample_ID')
                index1_column = row.index('index')
                index1_id_column = row.index('I7_Index_ID')
                try:
                    index2_column = row.index('index2')
                    index2_id_column = row.index('I5_Index_ID')
                except ValueError:
                    pass
                else:
                    dual_indexed = True

    if not indexing_data_set.has_unique_sample_ids():
        raise ValueError('Duplicate sample IDs detected in uploaded sample sheet(s).')

    if not indexing_data_set.has_unique_index_seqs():
        if dual_indexed:
            raise ValueError('Duplicate pairs of index sequences detected in uploaded sample sheet(s).')
        else:
            raise ValueError('Duplicate index sequences detected in uploaded sample sheet(s).')
    else:
        return indexing_data_set


def is_timed_out(start_time, timeout):
    return time.time() - start_time > timeout


def is_valid_sequence(sequence):
    if re.search('[^acgt,]', sequence, flags=re.IGNORECASE):
        raise ValueError(
            'Input sequences must be composed of valid bases (e.g., ACGT).')


def join_two_compatible_sets(a_sequences, b_sequences, b_is_self_compatible,
                             min_distance=3, length=float('inf')):
    if not b_is_self_compatible:
        if not is_self_compatible(b_sequences, min_distance, length):
            return None

    ab_sequences = []
    ab_sequences.extend(a_sequences)
    ab_sequences.extend(b_sequences)

    if is_self_compatible(ab_sequences, min_distance, length):
        return ab_sequences
    else:
        return None


def minimum_index_length_from_lists(*index_list, override_length=None):
    if override_length is None:
        index_list = [item for sublist in index_list for item in sublist]
        if len(index_list) > 0:
            return min([len(i) for i in index_list])
        else:
            return float('inf')
    else:
        return override_length


def minimum_index_length_from_sets(index_set_list):
    min_length = float('inf')
    for index_set in index_set_list:
        try:
            min_length = min(index_set.min_length(), min_length)
        except:
            pass
    return min_length


def is_self_compatible(index_list, min_distance=3, length=None):
    if len(index_list) == 0:
        return True

    if length is None:
        index_length = min(minimum_index_length_from_lists(index_list), float('inf'))
    else:
        index_length = length

    for pair in itertools.combinations(index_list, 2):
        distance = hamming_distance(
            pair[0][0:index_length].upper(), pair[1][0:index_length].upper())
        if distance < min_distance:
            return False
    return True


def optimize_set_order(*index_set_list):
    ordering = range(len(index_set_list))
    set_lengths = []
    seq_lengths = []

    for index_set in index_set_list:
        try:
            set_lengths.append(len(index_set.index_set.all()))
            seq_lengths.append(index_set.min_length())
        except:
            set_lengths.append(float('inf'))
            seq_lengths.append(0)

    return [o for (stl, sql, o) in sorted(
        zip(set_lengths, seq_lengths, ordering), key=lambda x: (-x[1], x[0]))]


def remove_incompatible_indexes_from_queryset(index_set, index_list, min_distance=3, length=float('inf')):
    if index_list == []:
        return index_set

    index_length = min(minimum_index_length_from_lists(index_set, index_list), length)
    incompatible_indexes = []

    for seq_1, seq_2 in itertools.product(index_set, index_list):
        distance = hamming_distance(
            seq_1[0:index_length].upper(),
            seq_2[0:index_length].upper())
        if distance < min_distance:
            incompatible_indexes.append(seq_1)

    return [i for i in index_set if i not in incompatible_indexes]


def reverse_complement(seq):
    return seq.translate(str.maketrans('ACGTacgt', 'TGCAtgca'))[::-1]
