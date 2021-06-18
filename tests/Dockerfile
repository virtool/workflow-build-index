FROM virtool/external-tools:0.2.0

RUN pip install poetry==1.1.6
WORKDIR /test

COPY ./pyproject.toml .
COPY ./poetry.lock .
RUN poetry install

COPY . .

ENTRYPOINT ["poetry", "run", "pytest"]
