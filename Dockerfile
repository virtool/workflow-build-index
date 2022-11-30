FROM virtool/workflow:5.2.1 as base
WORKDIR /workflow
COPY workflow.py utils.py /workflow/

FROM base as test
WORKDIR /test
RUN curl -sSL https://install.python-poetry.org | python3 -
COPY ./pyproject.toml ./poetry.lock ./
RUN poetry install
COPY . .
RUN ["poetry", "run", "pytest"]
