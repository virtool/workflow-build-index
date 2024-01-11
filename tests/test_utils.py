from types import GeneratorType

import pytest
from syrupy import SnapshotAssertion

from utils import get_sequences_from_patched_otus


@pytest.fixture()
def fake_otus():
    return [
        {
            "_id": "foo",
            "isolates": [
                {
                    "id": "foo_1",
                    "default": True,
                    "sequences": [
                        {"_id": "1", "sequence": "AGAGGATAGAGACACA"},
                        {"_id": "2", "sequence": "GGGTAGTCGATCTGGC"},
                    ],
                },
                {
                    "id": "foo_2",
                    "default": False,
                    "sequences": [
                        {"_id": "3", "sequence": "TTTAGAGTTGGATTAC", "default": True},
                        {"_id": "4", "sequence": "AAAGGAGAGAGAAACC", "default": True},
                    ],
                },
            ],
        },
        {
            "_id": "bar",
            "isolates": [
                {
                    "id": "bar_1",
                    "default": True,
                    "sequences": [
                        {"_id": "5", "sequence": "TTTGAGCCACACCCCC"},
                        {"_id": "6", "sequence": "GCCCACCCATTAGAAC"},
                    ],
                },
            ],
        },
    ]


@pytest.mark.parametrize("data_type", ["genome", "barcode"])
def test_get_sequences_from_patched_otus(
    data_type: str,
    fake_otus: list[dict],
    snapshot: SnapshotAssertion,
):
    sequence_otu_dict = {}

    sequences = get_sequences_from_patched_otus(fake_otus, data_type, sequence_otu_dict)

    assert isinstance(sequences, GeneratorType)
    assert list(sequences) == snapshot(name="sequences")
    assert sequence_otu_dict == snapshot(name="sequence_otu_dict")
