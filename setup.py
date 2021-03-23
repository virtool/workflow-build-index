from pathlib import Path
from setuptools import setup, find_packages

AUTHORS = ["Tiansheng Sui"]

CLASSIFIERS = [
    "Topic :: Software Development :: Libraries",
    "Programming Language:: Python:: 3.9",
]

PACKAGES = find_packages(exclude="tests")


INSTALL_REQUIRES = [
    "virtool-core==0.1.1",
    "virtool-workflow==0.4.0"
]

setup(
    name="vt-workflow-build-index",
    version="0.1.0",
    description="A workflow for building Virtool reference indexes.",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/virtool/workflow-build-index",
    author=", ".join(AUTHORS),
    license="MIT",
    platforms="linux",
    packages=PACKAGES,
    install_requires=INSTALL_REQUIRES,
    python_requires=">=3.9",
)