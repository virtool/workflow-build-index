import asyncio
from pathlib import Path

from pyfixtures import fixture


@fixture
async def bowtie_path(work_path: Path) -> Path:
    """The path to the generated Bowtie2 index files."""
    path = work_path / "bowtie"
    await asyncio.to_thread(path.mkdir)

    return path / "reference"


@fixture
async def export_json_path(work_path: Path) -> Path:
    """The path to the generated JSON index export file."""
    return work_path / "reference.json.gz"


@fixture
async def fasta_path(work_path: Path) -> Path:
    """The path to the generated index file."""
    return work_path / "reference.fa"
