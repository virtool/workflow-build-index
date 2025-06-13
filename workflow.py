import asyncio
import os
from pathlib import Path

from virtool.utils import compress_file
from virtool_workflow import RunSubprocess, hooks, step
from virtool_workflow.data.indexes import WFNewIndex

from utils import write_export_json_and_fasta


@hooks.on_failure
async def delete_index(new_index: WFNewIndex):
    await new_index.delete()


@step(name="Process OTUs")
async def process_otus(
    export_json_path: Path,
    fasta_path: Path,
    logger,
    new_index: WFNewIndex,
    proc: int,
    work_path: Path,
):
    """Create a FASTA file and exportable JSON from the index OTUs."""
    json_path = work_path / "reference.json"

    await asyncio.to_thread(
        write_export_json_and_fasta,
        new_index.reference,
        new_index.otus_json_path,
        json_path,
        fasta_path,
    )

    logger.info("wrote json file", stats=os.stat(json_path))

    await asyncio.to_thread(compress_file, json_path, export_json_path, processes=proc)


@step
async def bowtie_build(
    bowtie_path: Path,
    fasta_path: Path,
    proc: int,
    run_subprocess: RunSubprocess,
):
    """Build a Bowtie2 mapping index for the reference.

    Do not run the build if the reference contains barcode targets. Amplicon workflows
    do not use Bowtie2 indexes. The root name for the new reference is 'reference'.

    """
    await run_subprocess(["bowtie2-build", "--threads", proc, fasta_path, bowtie_path])


@step
async def finalize(
    bowtie_path: Path,
    export_json_path: Path,
    fasta_path: Path,
    new_index: WFNewIndex,
    proc: int,
    work_path: Path,
):
    """Compress and save the new reference index files."""
    compressed_fasta_path = work_path / "reference.fa.gz"

    await asyncio.to_thread(
        compress_file,
        fasta_path,
        compressed_fasta_path,
        processes=proc,
    )

    await new_index.upload(export_json_path)
    await new_index.upload(compressed_fasta_path)

    for filename in bowtie_path.parent.iterdir():
        await new_index.upload(bowtie_path.parent / filename)

    await new_index.finalize()
