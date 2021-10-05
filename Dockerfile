FROM virtool/workflow:nightly

WORKDIR /workflow

COPY workflow.py /workflow/workflow.py
COPY fixtures.py /workflow/fixtures.py
COPY utils.py /workflow/utils.py