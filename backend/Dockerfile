FROM python:3.13-slim

WORKDIR /finance_tracker

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

RUN poetry add prometheus-client

COPY . .

RUN poetry install --no-interaction --no-ansi

CMD ["uvicorn", "finance_tracker.main:app", "--host", "0.0.0.0", "--port", "8000"]