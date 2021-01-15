import os

from virtool_workflow import fixture
from virtool_workflow_runtime.db import VirtoolDatabase
from virtool_workflow_runtime.config.configuration import db_name, db_connection_string


@fixture
def db():
    return VirtoolDatabase(db_name(), db_connection_string())


@fixture
def job_params(job_args, db, data_path, index_path, temp_path):
    job_params = dict(job_args)

    job_params["reference_path"] = os.path.join(
        data_path,
        "references",
        job_args["ref_id"]
    )

    job_params["index_path"] = index_path

    job_params["temp_index_path"] = os.path.join(
        temp_path,
        job_params["index_id"]
    )

    document = await db.references.find_one(job_params["ref_id"], ["data_type"])

    job_params["data_type"] = document["data_type"]

    return job_params
