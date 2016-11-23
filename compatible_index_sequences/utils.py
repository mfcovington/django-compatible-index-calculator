import codecs
import csv
import itertools


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


def minimum_index_length(index_list):
    return min([len(i) for i in index_list])


def is_self_compatible(index_list, min_distance=3, length=float('inf')):
    index_length = min(minimum_index_length(index_list), length)
    for pair in itertools.combinations(index_list, 2):
        distance = hamming_distance(
            pair[0][0:index_length].upper(), pair[1][0:index_length].upper())
        if distance < min_distance:
            return False
    return True


def remove_incompatible_indexes_from_queryset(index_set, index_list, min_distance=3, length=float('inf')):
    index_length = min(index_set.min_length(), minimum_index_length(index_list), length)
    incompatible_indexes = []

    for index_1, seq_2 in itertools.product(index_set.index_set.all(), index_list):
        seq_1 = index_1.sequence
        distance = hamming_distance(seq_1[0:index_length], seq_2[0:index_length])
        if distance < min_distance:
            incompatible_indexes.append(index_1)

    return index_set.index_set.exclude(pk__in=[i.pk for i in incompatible_indexes])
