import itertools


def find_incompatible_index_pairs(index_list, min_distance=3):
    index_length = minimum_index_length(index_list)
    incompatible_pairs = []
    for pair in itertools.combinations(index_list, 2):
        distance = hamming_distance(
            pair[0][0:index_length], pair[1][0:index_length])
        if distance < min_distance:
            incompatible_pairs.append(pair)
    return incompatible_pairs


def hamming_distance(this, that):
    if not this or not that or len(this) != len(that):
        return None
    elif this == that:
        return 0
    else:
        return sum(1 for a, b in zip(this, that) if a != b)


def minimum_index_length(index_list):
    return min([len(i) for i in index_list])
