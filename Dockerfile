FROM python:3.13-bookworm AS uv
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}" \
    UV_CACHE_DIR='/tmp/uv_cache'
COPY uv.lock pyproject.toml README.md ./
RUN uv sync

FROM python:3.13-bookworm AS deps
COPY --from=ghcr.io/virtool/tools:1.1.0 /tools/bowtie2/2.5.4/bowtie* /usr/local/bin/
COPY --from=ghcr.io/virtool/tools:1.1.0 /tools/pigz/2.8/pigz /usr/local/bin/

FROM deps AS base 
WORKDIR /app
ENV PATH="/app/.venv/bin:${PATH}"
COPY --from=uv /app/.venv /app/.venv
COPY fixtures.py utils.py workflow.py VERSION* ./

FROM deps AS test
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}" \
    UV_CACHE_DIR='/tmp/uv_cache'
COPY uv.lock pyproject.toml README.md ./
COPY tests ./tests
COPY fixtures.py utils.py workflow.py ./
