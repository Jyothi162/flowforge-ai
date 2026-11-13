
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(
    title="FlowForge AI",
    description="Intelligent Business Automation Platform",
    version="1.0.0",
)


class CustomerRequest(BaseModel):
    customer_name: str = Field(min_length=1)
    email: str
    message: str = Field(min_length=1)
    priority: Literal["low", "medium", "high"] = "medium"


@app.get("/")
def home():
    return {
        "project": "FlowForge AI",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/requests")
def create_request(request: CustomerRequest):
    return {
        "request_id": str(uuid4()),
        "customer_name": request.customer_name,
        "email": request.email,
        "message": request.message,
        "priority": request.priority,
        "status": "received",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
