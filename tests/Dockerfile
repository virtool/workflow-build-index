FROM virtool/external-tools:0.2.0

RUN pip install poetry
WORKDIR test

COPY ./pyproject.toml .
COPY ./poetry.lock .
RUN poetry install

COPY . .

ENTRYPOINT ["poetry", "run", "pytest"]
