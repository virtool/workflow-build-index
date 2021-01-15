import asyncio
import json
import os
import shutil
import typing

import aiofiles
import virtool_core.history.db
import virtool_core.otus.utils
from virtool_workflow import step

import utils


@step
async def mk_index_dir(job_params, run_in_executor):
    """
    Make dir for the new index at ``<data_path>/references/<index_id>``.

    """
    await run_in_executor(
        os.makedirs,
        job_params["temp_index_path"]
    )


@step
async def write_fasta(job_params, db, data_path):
    """
    Generates a FASTA file of all sequences in the reference database. The FASTA headers are
    the accession numbers.
    """
    patched_otus = await get_patched_otus(
        db,
        data_path,
        job_params["manifest"]
    )

    sequence_otu_map = dict()

    sequences = get_sequences_from_patched_otus(
        patched_otus,
        job_params["data_type"],
        sequence_otu_map
    )

    fasta_path = os.path.join(job_params["temp_index_path"], "ref.fa")

    await write_sequences_to_file(fasta_path, sequences)

    index_id = job_params["index_id"]

    await db.indexes.update_one({"_id": index_id}, {
        "$set": {
            "sequence_otu_map": sequence_otu_map
        }
    })


@step
async def bowtie_build(job_params, number_of_processes, run_subprocess):
    """
    Run a standard bowtie-build process using the previously generated FASTA reference.
    The root name for the new reference is 'reference'
    """
    if job_params["data_type"] != "barcode":
        command = [
            "bowtie2-build",
            "-f",
            "--threads", str(number_of_processes),
            os.path.join(job_params["temp_index_path"], "ref.fa"),
            os.path.join(job_params["temp_index_path"], "reference")
        ]

        await run_subprocess(command)


@step
async def upload(job_params, db, run_in_executor):
    """
    Replaces the old index with the newly generated one.
    """
    await run_in_executor(
        shutil.copytree,
        job_params["temp_index_path"],
        job_params["index_path"]
    )

    # Tell the client the index is ready to be used and to no longer show it as building.
    await db.indexes.find_one_and_update({"_id": job_params["index_id"]}, {
        "$set": {
            "ready": True
        }
    })

    # Find OTUs with changes.
    pipeline = [
        {"$project": {
            "reference": True,
            "version": True,
            "last_indexed_version": True,
            "comp": {"$cmp": ["$version", "$last_indexed_version"]}
        }},
        {"$match": {
            "reference.id": job_params["ref_id"],
            "comp": {"$ne": 0}
        }},
        {"$group": {
            "_id": "$version",
            "id_list": {
                "$addToSet": "$_id"
            }
        }}
    ]

    id_version_key = {agg["_id"]: agg["id_list"] async for agg in db.otus.aggregate(pipeline)}

    # For each version number
    for version, id_list in id_version_key.items():
        await db.otus.update_many({"_id": {"$in": id_list}}, {
            "$set": {
                "last_indexed_version": version
            }
        })


@step
async def build_json(job_params, db, data_path, run_in_executor):
    """
    Create a reference.json.gz file at ``<data_path>/references/<ref_id>/<index_id>``.
    """
    document = await db.references.find_one(job_params["ref_id"], ["data_type", "organism", "targets"])

    otu_list = await utils.export(
        db,
        data_path,
        job_params["ref_id"]
    )

    data = {
        "otus": otu_list,
        "data_type": document["data_type"],
        "organism": document["organism"]
    }

    try:
        data["targets"] = document["targets"]
    except KeyError:
        pass

    file_path = os.path.join(
        job_params["index_path"],
        "reference.json.gz")

    # Convert the list of OTUs to a JSON-formatted string.
    json_string = json.dumps(data)

    # Compress the JSON string to a gzip file.
    await run_in_executor(utils.compress_json_with_gzip,
                          json_string,
                          file_path)

    await db.indexes.find_one_and_update({"_id": job_params["index_id"]}, {
        "$set": {
            "has_json": True
        }
    })


async def get_patched_otus(db, data_path, manifest: dict) -> typing.List[dict]:
    coros = list()

    for patch_id, patch_version in manifest.items():
        coros.append(virtool_core.history.db.patch_to_version(
            db,
            data_path,
            patch_id,
            patch_version
        ))

    return [j[1] for j in await asyncio.tasks.gather(*coros)]


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


async def write_sequences_to_file(path: str, sequences: typing.Iterable):
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
