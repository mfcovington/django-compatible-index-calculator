import codecs
import csv
import itertools
from .models import Index


def find_incompatible_index_pairs(index_list, min_distance=3):
    index_length = minimum_index_length(index_list)
    incompatible_pairs = []
    for pair in itertools.combinations(index_list, 2):
        distance = hamming_distance(
            pair[0][0:index_length], pair[1][0:index_length])
        if distance < min_distance:
            incompatible_pairs.append(pair)
    return incompatible_pairs


def generate_alignment(this, that):
    return ''.join(['|' if a == b else ' ' for a, b in zip(this, that)])


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


def lookup_index_set(index, complete_index_set=Index):
    return complete_index_set.objects.filter(sequence=index)


def minimum_index_length(index_list):
    return min([len(i) for i in index_list])
