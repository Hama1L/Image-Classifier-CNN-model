from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.model import predict
from app.schemas import Prediction, PredictionResponse

app = FastAPI(title="Image Classifier API", version="1.0.0")

# CORS is wide open here for local learning/dev convenience.
# Tighten allow_origins to your real frontend domain before shipping this anywhere public.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@app.get("/health")
def health_check() -> dict:
    """Used by Docker/monitoring to check the service is alive."""
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
async def classify_image(file: UploadFile = File(...)) -> PredictionResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Please upload a JPEG, PNG, or WEBP image.",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        results = predict(image_bytes, top_k=3)
    except Exception as exc:  # noqa: BLE001 - surface a clean error to the client
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc

    return PredictionResponse(
        predictions=[Prediction(label=label, confidence=conf) for label, conf in results]
    )


# Serve the frontend as static files. This mount MUST be last: FastAPI matches
# routes top-to-bottom, and StaticFiles would otherwise swallow /health and /predict.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
