from virtool_workflow import step, fixture, hooks
from virtool_core.utils import compress_file

BOWTIE_LINE_ENDINGS = (
    ".1.bt2", ".2.bt2", ".3.bt2", ".4.bt2",
    ".rev.1.bt2", ".rev.2.bt2",
)


@hooks.on_failure
async def delete_index(index_provider):
    await index_provider.delete()


@fixture
def index(indexes):
    return indexes[0]


@step
async def bowtie_build(index, proc):
    """
    Build a Bowtie2 mapping index for the reference.

    Do not run the build if the reference contains barcode targets. Amplicon workflows
    do not use Bowtie2 indexes. The root name for the new reference is 'reference'.

    """
    if index.reference.data_type != "barcode":
        await index.build_isolate_index(
            otu_ids=list(index.manifest.keys()),
            path=index.path/"reference",
            processes=proc
        )


@step
async def finalize(index, logger, run_in_executor):
    """Compress and save the new reference index files."""
    await run_in_executor(
        compress_file, index.path / "reference.fa",
        target=index.path / "reference.fa.gz"
    )

    await index.upload(index.path/"reference.fa.gz")

    for ending in BOWTIE_LINE_ENDINGS:
        await index.upload(index.bowtie_path.with_suffix(ending))

    await index.finalize()
