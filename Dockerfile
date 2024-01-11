FROM debian:buster as prep
WORKDIR /build
RUN apt-get update && apt-get install -y make gcc zlib1g-dev wget unzip
RUN wget https://zlib.net/pigz/pigz-2.8.tar.gz && \
    tar -xzvf pigz-2.8.tar.gz && \
    cd pigz-2.8 && \
    make
RUN wget https://github.com/BenLangmead/bowtie2/releases/download/v2.3.2/bowtie2-2.3.2-legacy-linux-x86_64.zip && \
    unzip bowtie2-2.3.2-legacy-linux-x86_64.zip && \
    mkdir bowtie2 && \
    cp bowtie2-2.3.2-legacy/bowtie2* bowtie2

FROM python:3.10-buster as base
WORKDIR /workflow
COPY --from=prep /build/bowtie2/* /usr/local/bin/
COPY --from=prep /build/pigz-2.8/pigz /usr/local/bin/pigz
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="/root/.local/bin:${PATH}"
COPY pyproject.toml poetry.lock utils.py workflow.py ./
RUN poetry export > requirements.txt
RUN pip install -r requirements.txt

FROM base as test
RUN poetry export  --with dev > requirements.txt
RUN pip install -r requirements.txt
COPY tests ./tests
RUN pytest
