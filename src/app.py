"""Smart Healthcare System API."""

import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from src.auth import SESSION_COOKIE, authenticate, create_session, create_user, delete_session, get_user, initialize_auth
from src.common.artifacts import validate_artifacts

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = ROOT / "new frontend" / "dist"
sys.path.append(str(ROOT / "scripts"))

load_dotenv(ROOT / ".env")
initialize_auth()
validate_artifacts()

from predict_diabetes import predict_diabetes
from predict_heart import predict_heart
from health_coach import generate_advice

app = FastAPI(
    title="Smart Healthcare System API",
    description="Predict Heart Disease and Diabetes",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------- Pydantic Models -------------------

class DiabetesInput(BaseModel):
    gender: str = Field(..., examples=["Female"])
    age: float = Field(..., ge=0, le=120, examples=[54.0])
    hypertension: int = Field(..., ge=0, le=1, examples=[0])
    heart_disease: int = Field(..., ge=0, le=1, examples=[0])
    smoking_history: str = Field(..., examples=["No Info"])
    bmi: float = Field(..., ge=10, le=80, examples=[27.32])
    HbA1c_level: float = Field(..., ge=2, le=20, examples=[6.6])
    blood_glucose_level: float = Field(..., ge=20, le=600, examples=[80.0])


class HeartInput(BaseModel):
    age: int = Field(..., ge=18, le=120, json_schema_extra={"example": 54})
    sex: str = Field(..., json_schema_extra={"example": "Male"})
    cp: str = Field(..., json_schema_extra={"example": "typical angina"})
    trestbps: int = Field(..., ge=60, le=300, json_schema_extra={"example": 140})
    chol: int = Field(..., ge=50, le=800, json_schema_extra={"example": 250})
    fbs: int = Field(..., ge=0, le=1, json_schema_extra={"example": 0})
    restecg: str = Field(..., json_schema_extra={"example": "normal"})
    thalch: int = Field(..., ge=40, le=250, json_schema_extra={"example": 150})
    exang: int = Field(..., ge=0, le=1, json_schema_extra={"example": 0})
    oldpeak: float = Field(..., ge=-5, le=20, json_schema_extra={"example": 1.5})
    slope: str = Field(..., json_schema_extra={"example": "flat"})
    ca: int = Field(..., ge=0, le=4, json_schema_extra={"example": 0})
    thal: str = Field(..., json_schema_extra={"example": "normal"})
    hypertension: Optional[str] = Field(default="No", examples=["No"])
    heightCm: Optional[float] = Field(default=None, ge=50, le=250, examples=[170])
    weightKg: Optional[float] = Field(default=None, ge=2, le=300, examples=[70])
    bmi: Optional[float] = Field(default=None, ge=10, le=80, examples=[24.2])
    diabetes: Optional[str] = Field(default="No", examples=["No"])
    smoking: Optional[str] = Field(default="No", examples=["No"])
    alcohol: Optional[str] = Field(default="No", examples=["No"])
    exercise: Optional[str] = Field(default="Yes", examples=["Yes"])
    familyHistory: Optional[str] = Field(default="No", examples=["No"])
    diet: Optional[str] = Field(default="Yes", examples=["Yes"])
    stress: Optional[str] = Field(default="No", examples=["No"])


class AdviceRequest(BaseModel):
    disease: str = Field(..., json_schema_extra={"example": "heart"})
    risk_level: str = Field(..., json_schema_extra={"example": "Moderate"})
    data: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str = Field(..., json_schema_extra={"example": "What foods should I avoid?"})
    disease: str = Field(default="", json_schema_extra={"example": "heart"})
    risk_level: str = Field(default="", json_schema_extra={"example": "Moderate"})
    data: Dict[str, Any] = Field(default_factory=dict)


class Credentials(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=6, max_length=200)


def current_user(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    user = get_user(session)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


# ------------------- Basic Endpoints -------------------

@app.get("/")
def home():
    index = FRONTEND_DIST / "index.html"
    return FileResponse(index if index.exists() else ROOT / "frontend" / "index.html")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/auth/register", status_code=201)
def register(credentials: Credentials):
    if not credentials.name or not credentials.name.strip():
        raise HTTPException(status_code=422, detail="Name is required.")
    try:
        return create_user(credentials.name, credentials.email, credentials.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/auth/login")
def login(credentials: Credentials, response: Response):
    try:
        user = authenticate(credentials.email, credentials.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    response.set_cookie(SESSION_COOKIE, create_session(user["id"]), httponly=True, secure=False, samesite="lax", max_age=604800)
    return user


@app.post("/auth/logout", status_code=204)
def logout(response: Response, session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    delete_session(session)
    response.delete_cookie(SESSION_COOKIE)


@app.get("/auth/me")
def me(user=Depends(current_user)):
    return user


# ------------------- Prediction Endpoints -------------------

@app.post("/predict/diabetes")
def api_predict_diabetes(data: DiabetesInput, user=Depends(current_user)):
    try:
        return predict_diabetes(data.model_dump())
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail="Invalid diabetes input.") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Prediction service unavailable.") from exc


@app.post("/predict/heart")
def api_predict_heart(data: HeartInput, user=Depends(current_user)):
    try:
        return predict_heart(data.model_dump())
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail="Invalid heart input.") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Prediction service unavailable.") from exc


@app.post("/extract-report")
async def api_extract_report(file: UploadFile = File(...), disease: str = Form("heart"), user=Depends(current_user)):
    """Extract heart-screening fields from a report image using Gemini Vision."""
    if file.content_type not in {"image/png", "image/jpeg", "image/jpg", "image/webp"}:
        raise HTTPException(status_code=400, detail="Upload a PNG, JPG, JPEG, or WEBP image.")
    try:
        from chatbot import extract_report_fields
        contents = await file.read(5 * 1024 * 1024 + 1)
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Report image must be 5 MB or smaller.")
        return extract_report_fields(contents, file.content_type, disease)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Could not extract report data.") from exc


# ------------------- Rule-Based Advice Endpoint -------------------

@app.post("/advice")
def api_get_advice(request: AdviceRequest, user=Depends(current_user)):
    try:
        return generate_advice(request.disease, request.risk_level, request.data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Advice service unavailable.") from exc


# ------------------- Gemini Chatbot Endpoint -------------------

@app.post("/chat")
def api_chat(request: ChatRequest, user=Depends(current_user)):
    try:
        from chatbot import get_chat_response
        reply = get_chat_response(
            message=request.message,
            disease=request.disease,
            risk_level=request.risk_level,
            data=request.data,
        )
        return {"reply": reply}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Chat service unavailable.") from exc


# ------------------- Static Files -------------------

app.mount("/static", StaticFiles(directory=str(ROOT / "frontend")), name="static")
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="react-assets")