from virtool_workflow import fixture

BOWTIE2_SUFFIXES = (
    "1.bt2",
    "2.bt2",
    "3.bt2",
    "4.bt2",
    "rev.1.bt2",
    "rev.2.bt2"
)


@fixture
def fasta_path(work_path):
    return work_path / "index.fa"
