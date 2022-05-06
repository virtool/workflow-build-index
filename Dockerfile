FROM virtool/workflow:4.0.2

WORKDIR /workflow

COPY workflow.py /workflow/workflow.py
COPY utils.py /workflow/utils.py
