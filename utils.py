import gzip

import virtool_core.history.db


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
