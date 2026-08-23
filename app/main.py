import time

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from app.metrics import ERROR_COUNT, PREDICTION_COUNT, REQUEST_COUNT, REQUEST_LATENCY
from app.model import predict

app = FastAPI(title="MLOps Sentiment Analysis API", version="1.0.0")


class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    label: str
    score: float


@app.middleware("http")
async def track_request_metrics(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start

    endpoint = request.url.path
    method = request.method
    status = str(response.status_code)

    REQUEST_LATENCY.labels(method=method, endpoint=endpoint, status_code=status).observe(elapsed)
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status).inc()

    return response


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictResponse)
async def predict_endpoint(req: PredictRequest):
    try:
        result = predict(req.text)
        PREDICTION_COUNT.labels(label=result["label"]).inc()
        return result
    except Exception:
        ERROR_COUNT.inc()
        raise


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return PlainTextResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )
