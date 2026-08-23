FROM python:3.13-slim@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a AS builder

WORKDIR /build

COPY app/requirements.txt .
ENV PYTHONPATH=/install/lib/python3.13/site-packages
RUN pip install --no-cache-dir --prefix=/install \
      --index-url https://download.pytorch.org/whl/cpu \
      torch==2.13.0 \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt \
 && rm -rf \
      /install/lib/python3.13/site-packages/jaraco \
      /install/lib/python3.13/site-packages/jaraco.context-*.dist-info \
      /install/lib/python3.13/site-packages/setuptools \
      /install/lib/python3.13/site-packages/setuptools-*.dist-info \
      /install/lib/python3.13/site-packages/wheel \
      /install/lib/python3.13/site-packages/wheel-*.dist-info

COPY app/ ./app/

RUN python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')"


FROM gcr.io/distroless/python3-debian13:nonroot@sha256:6bfc400d0a6d89f50f5bbc0a4b4ff57214ae5c01647c3a74c2a0c8d830b4cc00

COPY --from=builder --chown=nonroot:nonroot /install/lib/python3.13/site-packages /app/site-packages
COPY --from=builder --chown=nonroot:nonroot /build/app /app/app
COPY --from=builder --chown=nonroot:nonroot /root/.cache/huggingface /home/nonroot/.cache/huggingface

WORKDIR /app

USER nonroot

ENV PYTHONPATH=/app/site-packages
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1
ENV HF_HOME=/home/nonroot/.cache/huggingface

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["/usr/bin/python3.13", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

ENTRYPOINT ["/usr/bin/python3.13", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
