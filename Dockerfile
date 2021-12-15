FROM virtool/workflow:1.0.7

WORKDIR /workflow

COPY workflow.py /workflow/workflow.py
COPY fixtures.py /workflow/fixtures.py
COPY utils.py /workflow/utils.py
