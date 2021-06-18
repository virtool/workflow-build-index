import os
import types

import aiohttp.test_utils
import pytest

import utils


@pytest.fixture
def fake_otus():
    return [
        {
            "_id": "foo",
            "isolates": [
                {
                    "id": "foo_1",
                    "default": True,
                    "sequences": [
                        {
                            "_id": "1",
                            "sequence": "AGAGGATAGAGACACA"
                        },
                        {
                            "_id": "2",
                            "sequence": "GGGTAGTCGATCTGGC"
                        }
                    ]
                },
                {
                    "id": "foo_2",
                    "default": False,
                    "sequences": [
                        {
                            "_id": "3",
                            "sequence": "TTTAGAGTTGGATTAC",
                            "default": True
                        },
                        {
                            "_id": "4",
                            "sequence": "AAAGGAGAGAGAAACC",
                            "default": True
                        }
                    ]
                },
            ]
        },
        {
            "_id": "bar",
            "isolates": [
                {
                    "id": "bar_1",
                    "default": True,
                    "sequences": [
                        {
                            "_id": "5",
                            "sequence": "TTTGAGCCACACCCCC"
                        },
                        {
                            "_id": "6",
                            "sequence": "GCCCACCCATTAGAAC"
                        }
                    ]
                }
            ]
        }
    ]


@pytest.mark.parametrize("data_type", ["genome", "barcode"])
def test_get_sequences_from_patched_otus(data_type, data_regression, fake_otus):
    sequence_otu_dict = dict()

    sequences = utils.get_sequences_from_patched_otus(
        fake_otus,
        data_type,
        sequence_otu_dict
    )

    assert isinstance(sequences, types.GeneratorType)

    data_regression.check(list(sequences), basename=f"sequences_{data_type}")
    data_regression.check(sequence_otu_dict, basename=data_type)


@pytest.mark.asyncio
async def test_write_sequences_to_file(file_regression, tmpdir):
    sequences = [
        {
            "_id": "foo",
            "sequence": "ATTGAGAGATAGAGACAC"
        },
        {
            "_id": "bar",
            "sequence": "GGGTACGAGTTTCTATCG"
        },
        {
            "_id": "baz",
            "sequence": "GGCTTCGGACTTTTTTCG"
        }
    ]

    path = os.path.join(str(tmpdir), "output.fa")

    await utils.write_sequences_to_file(path, sequences)

    with open(path, "r") as f:
        file_regression.check(f.read())
