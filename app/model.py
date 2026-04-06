from transformers import pipeline

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

_classifier = None


def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline("sentiment-analysis", model=MODEL_NAME)
    return _classifier


def predict(text: str) -> dict:
    classifier = get_classifier()
    result = classifier(text, truncation=True)[0]
    return {"label": result["label"], "score": round(result["score"], 4)}
