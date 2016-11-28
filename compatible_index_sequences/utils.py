import codecs
import csv
import itertools
import time
from collections import deque


def find_compatible_subset(index_set_list, subset_size_list, min_length,
                           previous_list=[], timeout=10, start_time=None):

    if start_time is None:
        start_time = time.time()
    compatible_subset = []

    index_set_list = deque(index_set_list)
    subset_size_list = deque(subset_size_list)

    try:
        index_set = index_set_list.popleft()
        current_list = [i.sequence for i in index_set.index_set.all()]
    except:
        return []

    index_list = remove_incompatible_indexes_from_queryset(
        current_list, previous_list, length=min_length)
    subset_size = subset_size_list.popleft()

    if len(index_list) < subset_size:
        return []

    self_compatible_list = is_self_compatible(index_list, length=min_length)

    for index_subset in itertools.combinations(index_list, subset_size):

        if not self_compatible_list:
            if not is_self_compatible(index_subset, length=min_length):
                if is_timed_out(start_time, timeout=timeout):
                    timed_out = True
                    return []
                continue
            else:
                compatible_subset = list(index_subset)
        else:
            compatible_subset = list(index_subset)

        if len(index_set_list) > 0:
            previous_list.extend(compatible_subset)
            new_list = find_compatible_subset(
                index_set_list, subset_size_list, min_length, previous_list,
                timeout, start_time)
            if new_list:
                compatible_subset.extend(new_list)
            else:
                compatible_subset = []

        if compatible_subset:
            break

    return compatible_subset


def find_incompatible_index_pairs(index_list, min_distance=3):
    index_length = minimum_index_length(index_list)
    incompatible_pairs = []
    for pair in itertools.combinations(index_list, 2):
        distance = hamming_distance(
            pair[0][0:index_length].upper(), pair[1][0:index_length].upper())
        if distance < min_distance:
            incompatible_pairs.append(pair)
    return incompatible_pairs


def generate_alignment(this, that):
    return ''.join(
        ['|' if a == b else ' ' for a, b in zip(this.upper(), that.upper())])


def hamming_distance(this, that):
    if not this or not that or len(this) != len(that):
        return None
    elif this == that:
        return 0
    else:
        return sum(1 for a, b in zip(this, that) if a != b)


def index_list_from_samplesheet(request):
    index_list = []
    file = request.FILES.get('samplesheet')

    if file:
        reader = csv.reader(codecs.iterdecode(file, 'utf-8'))
        ok = 0
        for row in reader:
            if ok == 1:
                index_list.append(row[5])
            if row[0] == 'Sample_ID':
                ok = 1

    return index_list


def is_timed_out(start_time, timeout):
    return time.time() - start_time > timeout


def join_two_compatible_sets(a_sequences, b_sequences, b_is_self_compatible,
                             length=float('inf')):
    if not b_is_self_compatible:
        if not is_self_compatible(b_sequences, length=length):
            return None

    ab_sequences = []
    ab_sequences.extend(a_sequences)
    ab_sequences.extend(b_sequences)

    if is_self_compatible(ab_sequences, length=length):
        return ab_sequences
    else:
        return None


def minimum_index_length(*index_list):
    index_list = [item for sublist in index_list for item in sublist]
    return min([len(i) for i in index_list])


def is_self_compatible(index_list, min_distance=3, length=float('inf')):
    index_length = min(minimum_index_length(index_list), length)
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

    index_length = min(minimum_index_length(index_set, index_list), length)
    incompatible_indexes = []

    for seq_1, seq_2 in itertools.product(index_set, index_list):
        distance = hamming_distance(seq_1[0:index_length], seq_2[0:index_length])
        if distance < min_distance:
            incompatible_indexes.append(seq_1)

    return [i for i in index_set if i not in incompatible_indexes]
