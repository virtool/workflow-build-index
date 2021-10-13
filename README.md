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

#### Docker Container With External Dependencies Installed

```shell script
cd tests && docker-compose up
```

### Commits

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0) specification.

These standardized commit messages are used to automatically publish releases using [`semantic-release`](https://semantic-release.gitbook.io/semantic-release)
after commits are merged to `main` from successful PRs.

**Example**

```text
feat: add API support for assigning labels to existing samples
```

Descriptive bodies and footers are required where necessary to describe the impact of the commit. Use bullets where appropriate.

Additional Requirements
1. **Write in the imperative**. For example, _"fix bug"_, not _"fixed bug"_ or _"fixes bug"_.
2. **Don't refer to issues or code reviews**. For example, don't write something like this: _"make style changes requested in review"_.
Instead, _"update styles to improve accessibility"_.
3. **Commits are not your personal journal**. For example, don't write something like this: _"got server running again"_
or _"oops. fixed my code smell"_.

From Tim Pope: [A Note About Git Commit Messages](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html)
