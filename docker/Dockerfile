FROM python:3.12-slim AS builder

WORKDIR /build

COPY app/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY app/ ./app/

ENV PYTHONPATH=/install/lib/python3.12/site-packages
RUN python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')"


FROM python:3.12-slim

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

COPY --from=builder /install /usr/local
COPY --from=builder /build/app /app/app
COPY --from=builder /root/.cache/huggingface /home/appuser/.cache/huggingface

WORKDIR /app

RUN chown -R appuser:appuser /app /home/appuser

USER appuser

ENV TRANSFORMERS_OFFLINE=1
ENV HF_HOME=/home/appuser/.cache/huggingface

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
