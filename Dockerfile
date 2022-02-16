FROM virtool/workflow:2.0.0

WORKDIR /workflow

COPY workflow.py /workflow/workflow.py
COPY utils.py /workflow/utils.py
