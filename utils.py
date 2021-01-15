import asyncio
import gzip
import typing

import aiofiles
import virtool_core.history.db
import virtool_core.otus.utils

ISOLATE_KEYS = [
    "id",
    "source_type",
    "source_name",
    "default"
]

OTU_KEYS = [
    "name",
    "abbreviation",
    "schema"
]

RIGHTS = [
    "build",
    "modify",
    "modify_otu",
    "remove"
]

SEQUENCE_KEYS = [
    "accession",
    "definition",
    "host",
    "sequence"
]


async def get_patched_otus(db, data_path, manifest):
    coros = list()

    for patch_id, patch_version in manifest.items():
        coros.append(virtool_core.history.db.patch_to_version(
            db,
            data_path,
            patch_id,
            patch_version
        ))

    return [j[1] for j in await asyncio.tasks.gather(*coros)]


async def write_sequences_to_file(path, sequences):
    """
    Write a FASTA file based on a given `Iterable` containing sequence documents.
    Headers will contain the `_id` field of the document and the sequence text is from the `sequence` field.
    :param path: the path to write the file to
    :param sequences: the sequences to write to file
    """
    async with aiofiles.open(path, "w") as f:
        for sequence in sequences:
            sequence_id = sequence["_id"]
            sequence_data = sequence["sequence"]

            line = f">{sequence_id}\n{sequence_data}\n"
            await f.write(line)


def get_sequences_from_patched_otus(
        otus: typing.Iterable[dict],
        data_type: str, sequence_otu_map: dict
) -> typing.Generator[dict, None, None]:
    """
    Return sequence documents based on an `Iterable` of joined OTU documents. Writes a map of sequence IDs to OTU IDs
    into the passed `sequence_otu_map`.
    If `data_type` is `barcode`, all sequences are returned. Otherwise, only sequences of default isolates are returned.
    :param otus: an Iterable of joined OTU documents
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
            for sequence in virtool_core.otus.utils.extract_sequences(otu):
                yield sequence
        else:
            for sequence in virtool_core.otus.utils.extract_default_sequences(otu):
                yield sequence


async def export(db, data_path, ref_id):
    otu_list = list()

    query = {
        "reference.id": ref_id,
        "last_indexed_version": {
            "$ne": None
        }
    }

    async for document in db.otus.find(query):
        _, joined, _ = await virtool_core.history.db.patch_to_version(
            db,
            data_path,
            document["_id"],
            document["last_indexed_version"]
        )

        otu_list.append(joined)

    return clean_export_list(otu_list)


def clean_export_list(otus):
    cleaned = list()

    otu_keys = OTU_KEYS + ["_id"]
    sequence_keys = SEQUENCE_KEYS + ["_id"]

    for otu in otus:
        try:
            otu["_id"] = otu["remote"]["id"]
        except KeyError:
            pass

        for isolate in otu["isolates"]:
            for sequence in isolate["sequences"]:
                try:
                    sequence["_id"] = sequence["remote"]["id"]
                except KeyError:
                    pass

        cleaned.append(clean_otu(otu, otu_keys, sequence_keys))

    return cleaned


def clean_otu(otu, otu_keys=None, sequence_keys=None):
    otu_keys = otu_keys or OTU_KEYS
    sequence_keys = sequence_keys or SEQUENCE_KEYS

    cleaned = {key: otu.get(key) for key in otu_keys}

    cleaned.update({
        "isolates": list(),
        "schema": otu.get("schema", list())
    })

    for isolate in otu["isolates"]:
        cleaned_isolate = {key: isolate[key] for key in ISOLATE_KEYS}
        cleaned_isolate["sequences"] = list()

        for sequence in isolate["sequences"]:
            cleaned_sequence = {key: sequence[key] for key in sequence_keys}

            for key in ["segment", "target"]:
                try:
                    cleaned_sequence[key] = sequence[key]
                except KeyError:
                    pass

            cleaned_isolate["sequences"].append(cleaned_sequence)

        cleaned["isolates"].append(cleaned_isolate)

    return cleaned


def compress_json_with_gzip(json_string: str, target: str):
    """
    Compress the JSON string to a gzipped file at `target`.
    """
    with gzip.open(target, 'wb') as f:
        f.write(bytes(json_string, "utf-8"))
