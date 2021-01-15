import os
import types

import aiohttp.test_utils
import pytest
from virtool_workflow_runtime.config.configuration import db_name, db_connection_string
from virtool_workflow_runtime.db import VirtoolDatabase

import utils


@pytest.fixture()
def db():
    db = VirtoolDatabase(db_name(), db_connection_string())
    return db


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


@pytest.mark.asyncio
async def test_get_patched_otus(mocker, db):
    mocker.patch("virtool_core.history.db.patch_to_version", aiohttp.test_utils.make_mocked_coro((None, {"_id": "foo"}, None)))

    manifest = {
        "foo": 2,
        "bar": 10,
        "baz": 4
    }

    data_path = "foo"

    patched_otus = await utils.get_patched_otus(
        db,
        data_path,
        manifest
    )

    assert list(patched_otus) == [
        {"_id": "foo"},
        {"_id": "foo"},
        {"_id": "foo"}
    ]


@pytest.mark.parametrize("data_type", ["genome", "barcode"])
def test_get_sequences_from_patched_otus(data_type, snapshot, fake_otus):
    sequence_otu_dict = dict()

    sequences = utils.get_sequences_from_patched_otus(
        fake_otus,
        data_type,
        sequence_otu_dict
    )

    assert isinstance(sequences, types.GeneratorType)

    snapshot.assert_match(list(sequences))
    snapshot.assert_match(sequence_otu_dict)


@pytest.mark.asyncio
async def test_write_sequences_to_file(snapshot, tmpdir):
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
        snapshot.assert_match(f.read())