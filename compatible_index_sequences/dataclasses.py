from dataclasses import dataclass


@dataclass
class IndexingData:
    index_1_sequence: str
    index_1_name: str = None
    index_1_set_names: List(str) = None
    index_2_sequence: str = None
    index_2_name: str = None
    index_2_set_names: List(str) = None
    sample_id: str = None

    def indexing_type(self):
        if self.index_1_sequence is None:
            raise ValueError('The sequence for Index 1 (i7) is missing.')
        elif self.index_2_sequence is None:
            return 'single'
        else:
            return 'dual'
