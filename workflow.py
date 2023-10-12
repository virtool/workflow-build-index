import asyncio

from virtool_core.utils import compress_file
from virtool_workflow import step, fixture, hooks
from virtool_workflow.api.indexes import IndexProvider
from virtool_workflow.data_model.indexes import WFIndex

BOWTIE_LINE_ENDINGS = (
    ".1.bt2",
    ".2.bt2",
    ".3.bt2",
    ".4.bt2",
    ".rev.1.bt2",
    ".rev.2.bt2",
)


@hooks.on_failure
async def delete_index(index_provider: IndexProvider):
    await index_provider.delete()


@fixture
def index(indexes: list[WFIndex]) -> WFIndex:
    return indexes[0]


@step
async def bowtie_build(index: WFIndex, proc: int):
    """
    Build a Bowtie2 mapping index for the reference.

    Do not run the build if the reference contains barcode targets. Amplicon workflows
    do not use Bowtie2 indexes. The root name for the new reference is 'reference'.

    """
    if index.reference.data_type != "barcode":
        await index.build_isolate_index(
            otu_ids=list(index.manifest.keys()),
            path=index.path / "reference",
            processes=proc,
        )


@step
async def finalize(index: WFIndex):
    """Compress and save the new reference index files."""
    await asyncio.to_thread(
        compress_file,
        index.path / "reference.fa",
        target=index.path / "reference.fa.gz",
    )

    await asyncio.gather(
        index.upload(index.path / "reference.fa.gz"),
        *[
            index.upload(index.bowtie_path.with_suffix(ending))
            for ending in BOWTIE_LINE_ENDINGS
        ]
    )

    await index.finalize()
