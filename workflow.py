import json
import os
import shutil

import utils
import virtool_core.utils
from virtool_workflow import cleanup, step


@step
async def mk_index_dir(job_params, run_in_executor):
    """
    Make dir for the new index at ``<temp_path>/<index_id>``.
    """
    await run_in_executor(
        os.makedirs,
        job_params["temp_index_path"]
    )


@step
async def write_fasta(job_params, data_path, db):
    """
    Generates a FASTA file of all sequences in the reference database. The FASTA headers are
    the accession numbers.
    """
    patched_otus = await utils.get_patched_otus(
        db,
        data_path,
        job_params["manifest"]
    )

    sequence_otu_map = dict()

    sequences = utils.get_sequences_from_patched_otus(
        patched_otus,
        job_params["data_type"],
        sequence_otu_map
    )

    fasta_path = os.path.join(job_params["temp_index_path"], "ref.fa")

    await utils.write_sequences_to_file(fasta_path, sequences)

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


@cleanup
async def delete_index(job_params, db, run_in_executor):
    """
    Removes the nascent index document and directory.
    """
    await db.indexes.delete_one({"_id": job_params["index_id"]})

    try:
        await run_in_executor(
            virtool_core.utils.rm,
            job_params["index_path"],
            True
        )
    except FileNotFoundError:
        pass


@cleanup
async def reset_history(job_params, db):
    """
    Sets the index ID and version fields for all history items included in failed build to 'unbuilt'.
    """
    query = {
        "_id": {
            "$in": await db.history.distinct("_id", {"index.id": job_params["index_id"]})
        }
    }

    # Set all the otus included in the build to "unbuilt" again.
    await db.history.update_many(query, {
        "$set": {
            "index": {
                "id": "unbuilt",
                "version": "unbuilt"
            }
        }
    })
