import base64
import codecs
import csv
import itertools
import time
from collections import deque, OrderedDict

from weblogolib import (
    Alphabet, ColorScheme, LogoData, LogoFormat, LogoOptions, Seq, SeqList, SymbolColor,
    png_formatter)


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

    sample_ids = []
    index_list = []
    index_list_2 = []
    dual_indexed = False

    for file in file_list:
        if file is None:
            continue
        reader = csv.reader(codecs.iterdecode(file, 'utf-8'))
        header_done = False
        for row in reader:
            if header_done:
                sample_ids.append(row[sample_id_column])
                index_list.append(row[index1_column])
                if dual_indexed:
                    index_list_2.append(row[index2_column])
            if 'Sample_ID' in row:
                header_done = True
                sample_id_column = row.index('Sample_ID')
                index1_column = row.index('index')
                try:
                    index2_column = row.index('index2')
                except ValueError:
                    pass
                else:
                    dual_indexed = True

    if len(sample_ids) > len(set(sample_ids)):
        raise ValueError('Duplicate sample IDs detected in uploaded sample sheet(s).')

    if dual_indexed:
        index_list = [",".join([i1, i2]) for i1, i2 in zip(index_list, index_list_2)]
        if len(index_list) > len(set(index_list)):
            raise ValueError('Duplicate pairs of index sequences detected in uploaded sample sheet(s).')
        return OrderedDict(zip(index_list, sample_ids))
    else:
        if len(index_list) > len(set(index_list)):
            raise ValueError('Duplicate index sequences detected in uploaded sample sheet(s).')
        return OrderedDict(zip(index_list, sample_ids))


def is_timed_out(start_time, timeout):
    return time.time() - start_time > timeout


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


def minimum_index_length_from_lists(*index_list):
    index_list = [item for sublist in index_list for item in sublist]
    if len(index_list) > 0:
        return min([len(i) for i in index_list])
    else:
        return float('inf')


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


def weblogo_base64(index_list):
    illumina_colors = ColorScheme(
            [
                SymbolColor("G", "blue"),
                SymbolColor("T", "black"),
                SymbolColor("C", "green"),
                SymbolColor("A", "red")
            ],
    )
    ngs_bases = Alphabet('ACGT', zip('acgt', 'ACGT'))

    sequences = SeqList(
        (Seq(s, alphabet=ngs_bases) for s in index_list), alphabet=ngs_bases)
    data = LogoData.from_seqs(sequences)
    options = LogoOptions(
        color_scheme=illumina_colors,
        number_interval=1,
        show_fineprint=False,
    )

    logo = {}
    png = png_formatter(data, LogoFormat(data, options))
    logo['bit'] = base64.b64encode(png)

    options.unit_name = 'probability'
    png = png_formatter(data, LogoFormat(data, options))
    logo['probability'] = base64.b64encode(png)

    return logo
