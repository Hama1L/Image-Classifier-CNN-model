from pydantic import BaseModel, Field


class Prediction(BaseModel):
    label: str = Field(..., description="Predicted class name")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence, 0-1")


class PredictionResponse(BaseModel):
    predictions: list[Prediction]
