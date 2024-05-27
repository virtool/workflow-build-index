# workflow-build-index

A workflow for building Virtool reference indexes.

## Steps

1. Build index of default isolates using `bowtie2-build`.
2. Compress FASTA file.
3. Upload FASTA and Bowtie2 index files to server.
4. Finalize the index resource, which allows it to be used in analysis workflows.

## Contributing

### Unit Tests

#### Virtual Environment

```shell script
poetry install
poetry run pytest
```
