import gzip
import json
from collections.abc import Generator
from pathlib import Path

from virtool.references.models import ReferenceNested


def compress_json_with_gzip(json_string: str, path: Path):
    """Compress the JSON string to a gzipped file at `path`.

    :param json_string: the JSON string to compress
    :param path: the path to the target file
    """
    with gzip.open(path, "wt") as f:
        f.write(json_string)


def extract_default_sequences(joined: dict[str, dict]) -> list[dict]:
    """Return a list of sequences from the default isolate of the passed joined otu.

    :param joined: the joined otu document.
    :return: a list of sequences associated with the default isolate.
    """
    for isolate in joined["isolates"]:
        if isolate["default"]:
            return isolate["sequences"]

    return []


def extract_sequences(otu: dict[str, dict]) -> Generator[str, None, None]:
    """Extract sequences from an OTU document

    :param otu: The OTU document
    :return: a generator containing sequences from the isolates of the OTU
    """
    for isolate in otu["isolates"]:
        for sequence in isolate["sequences"]:
            yield sequence


def get_sequences_from_patched_otus(
    otus: list[dict],
    data_type: str,
    sequence_otu_map: dict,
) -> Generator[dict, None, None]:
    """Return sequence documents based on an `Iterable` of joined OTU documents. Writes
    a map of sequence IDs to OTU IDs into the passed `sequence_otu_map`.

    If `data_type` is `barcode`, all sequences are returned. Otherwise, only sequences
    of default isolates are returned.

    :param otus: joined OTU documents
    :param data_type: the data type of the parent reference for the OTUs
    :param sequence_otu_map: a dict to populate with sequence-OTU map information
    :return: a generator that yields sequence documents

    """
    for otu in otus:
        otu_id = otu["_id"]

        for isolate in otu["isolates"]:
            for sequence in isolate["sequences"]:
                sequence_id = sequence["_id"]
                sequence_otu_map[sequence_id] = otu_id

        if data_type == "barcode":
            for sequence in extract_sequences(otu):
                yield sequence
        else:
            for sequence in extract_default_sequences(otu):
                yield sequence


def prepare_exportable_otu(otu: dict) -> dict:
    """Prepare an OTU for export by:

    1. Replacing the OTU and sequence IDs with their remote IDs if they exist.
    2. Removing fields that shouldn't be exported.

    :param otu: the OTU to prepare
    :return: the prepared exportable OTU

    """
    try:
        otu_id = otu["remote"]["id"]
    except KeyError:
        otu_id = otu["_id"]

    cleaned_otu = {
        "_id": otu_id,
        **{
            key: otu[key]
            for key in (
                "name",
                "abbreviation",
                "schema",
            )
        },
        "isolates": [],
    }

    for isolate in otu["isolates"]:
        cleaned_isolate = {
            **{
                key: isolate[key]
                for key in (
                    "id",
                    "source_type",
                    "source_name",
                    "default",
                )
            },
            "sequences": [],
        }

        for sequence in isolate["sequences"]:
            try:
                sequence_id = sequence["remote"]["id"]
            except KeyError:
                sequence_id = sequence["_id"]

            cleaned_sequence = {
                "_id": sequence_id,
                **{
                    key: sequence[key]
                    for key in (
                        "accession",
                        "definition",
                        "host",
                        "sequence",
                    )
                },
                **{key: sequence.get(key) for key in ("segment", "target")},
            }

            cleaned_isolate["sequences"].append(cleaned_sequence)

        cleaned_otu["isolates"].append(cleaned_isolate)

    return cleaned_otu


def write_export_json_and_fasta(
    reference: ReferenceNested,
    otus_json_path: Path,
    json_path: Path,
    fasta_path: Path,
):
    with open(otus_json_path) as f:
        otus = json.load(f)

    with open(json_path, "w") as f_json, open(fasta_path, "w") as f_fasta:
        exportable_otus = []

        for otu in otus:
            for sequence in extract_default_sequences(otu):
                f_fasta.write(f">{sequence['_id']}\n{sequence['sequence']}\n")

            exportable_otus.append(prepare_exportable_otu(otu))

        json.dump(
            {
                "data_type": reference.data_type,
                "organism": "",
                "otus": exportable_otus,
                "targets": None,
            },
            f_json,
        )
