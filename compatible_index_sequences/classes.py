from dataclasses import dataclass, field
from typing import List


@dataclass
class IndexingData:
    """
    >>> i0 = IndexingData('CACACAC')
    >>> i0
    IndexingData(index_1_sequence='CACACAC', index_1_id=[], index_2_sequence=None, index_2_id=[], sample_id=None)
    >>> i1 = IndexingData('CACACAC', sample_id='Control')
    >>> i1
    IndexingData(index_1_sequence='CACACAC', index_1_id=[], index_2_sequence=None, index_2_id=[], sample_id='Control')
    >>> i2 = IndexingData('GTGTGTG', index_2_sequence='ATATATA')
    >>> i2
    IndexingData(index_1_sequence='GTGTGTG', index_1_id=[], index_2_sequence='ATATATA', index_2_id=[], sample_id=None)
    >>> i3 = IndexingData('AAAAAAA', index_1_id='INDEX 03')
    >>> i3
    IndexingData(index_1_sequence='AAAAAAA', index_1_id=['INDEX 03'], index_2_sequence=None, index_2_id=[], sample_id=None)
    >>> i4 = IndexingData('GTGTGTG', index_1_id='INDEX 03', index_2_sequence='ATATATA', index_2_id=['Set 1:INDEX 02', 'Set 5:INDEX 08'])
    >>> i4
    IndexingData(index_1_sequence='GTGTGTG', index_1_id=['INDEX 03'], index_2_sequence='ATATATA', index_2_id=['Set 1:INDEX 02', 'Set 5:INDEX 08'], sample_id=None)
    >>> i1.indexing_type()
    'single'
    >>> i2.indexing_type()
    'dual'
    """
    index_1_sequence: str
    index_1_id: List[str] = field(default_factory=list)
    index_2_sequence: str = None
    index_2_id: List[str] = field(default_factory=list)
    sample_id: str = None

    def __post_init__(self):
        if type(self.index_1_id) is not list:
            self.index_1_id = [self.index_1_id]
        if type(self.index_2_id) is not list:
            self.index_2_id = [self.index_2_id]

    def indexing_type(self):
        if self.index_1_sequence is None:
            raise ValueError('The sequence for Index 1 (i7) is missing.')
        elif self.index_2_sequence is None:
            return 'single'
        else:
            return 'dual'


@dataclass
class IndexingDataSet:
    """
    >>> i1 = IndexingData('CACACAC')
    >>> i2 = IndexingData('GTGTGTG')
    >>> i3 = IndexingData('AAAAAAA')
    >>> s1 = IndexingDataSet(i1)
    >>> s2 = IndexingDataSet([i2])

    >>> s1
    IndexingDataSet(index_data=[IndexingData(index_1_sequence='CACACAC', index_1_id=[], index_2_sequence=None, index_2_id=[], sample_id=None)])
    >>> s2  # doctest: +ELLIPSIS
    IndexingDataSet(index_data=[IndexingData(index_1_sequence='GTGTGTG', ...])

    >>> s1.add(i3)
    >>> s2.add(s1)

    >>> s1  # doctest: +ELLIPSIS
    IndexingDataSet(index_data=[IndexingData(index_1_sequence='CACACAC', ..., IndexingData(index_1_sequence='AAAAAAA', ...])
    >>> s2  # doctest: +ELLIPSIS
    IndexingDataSet(index_data=[IndexingData(index_1_sequence='GTGTGTG', ..., IndexingData(index_1_sequence='CACACAC', ..., IndexingData(index_1_sequence='AAAAAAA', ...])

    >>> s1.has_unique_index_seqs()
    True
    >>> s2.add(s2)
    >>> s2.has_unique_index_seqs()
    False

    >>> s1.get_index_1_sequences()
    ['CACACAC', 'AAAAAAA']
    >>> s2.get_index_1_sequences()
    ['GTGTGTG', 'CACACAC', 'AAAAAAA', 'GTGTGTG', 'CACACAC', 'AAAAAAA']
    """
    index_data: List[IndexingData] = field(default_factory=list)

    def __post_init__(self):
        if type(self.index_data) is IndexingData:
            self.index_data = [self.index_data]

    def add(self, other):
        if type(other) is IndexingData:
            self.index_data.append(other)
        elif type(other) is IndexingDataSet:
            self.index_data.extend(other.index_data)
        elif type(other) is str:
            if other.count(',') == 0:
                self.index_data.append(IndexingData(other))
            elif other.count(',') == 1:
                (index_1, index_2) = other.split(',')
                self.index_data.append(
                    IndexingData(index_1, index_2_sequence=index_2))
            elif other.count(',') > 1:
                raise TypeError('Unsupported type ...')    # Fix wording
        elif type(other) is List[str]:
            self.index_data.append([IndexingData(seq) for seq in other])
        elif type(other) is list:
            if all(isinstance(elem, str) for elem in other):
                self.index_data.append([IndexingData(seq) for seq in other])
            elif all(isinstance(elem, IndexingData) for elem in other):
                self.index_data.extend(other)
            else:
                raise TypeError('Unsupported type ...')    # Fix wording
        else:
            raise TypeError('Unsupported type ...')    # Fix wording

    def has_unique_index_seqs(self):
        index_seqs = [(sample.index_1_sequence, sample.index_2_sequence)
            for sample in self.index_data]
        if len(index_seqs) > len(set(index_seqs)):
            return False
        else:
            return True

    def has_unique_sample_ids(self):
        sample_ids = [sample.sample_id for sample in self.index_data]
        if len(sample_ids) > len(set(sample_ids)):
            return False
        else:
            return True

    def get_indexing_type(self):
        if len(self.index_data) == 0:
            return None
        index_2_seqs = [sample.index_2_sequence for sample in self.index_data]
        if len(list(filter(None, index_2_seqs))) == 0:
            return 'single'
        if len(list(filter(None, index_2_seqs))) == len(index_2_seqs):
            return 'dual'
        else:
            return 'mixed'

    def get_index_1_sequences(self):
        return [sample.index_1_sequence for sample in self.index_data]

    def get_index_2_sequences(self):
        return [sample.index_2_sequence for sample in self.index_data]

    def get_sample_ids(self):
        return ['' if sample.sample_id is None else sample.sample_id
            for sample in self.index_data]

    def _get_min_index_length(self, index_number):
        if index_number == 1:
            index_list = self.get_index_1_sequences()
        elif index_number == 2:
            index_list = self.get_index_2_sequences()
        else:
            raise ValueError('Must choose index number of 1 or 2.')
        index_list = [item for sublist in index_list for item in sublist]
        if len(index_list) > 0:
            return min([len(i) for i in index_list])
        else:
            return float('inf')

    def min_index_1_length(self):
        return _get_min_index_length(1)

    def min_index_2_length(self):
        return _get_min_index_length(2)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
