
import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flowforge")


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="FlowForge AI",
    description="Intelligent Business Automation Platform",
    version="1.0.0",
)


# --------------------------------------------------
# Environment Configuration
# --------------------------------------------------

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://localhost:5678/webhook/customer-request",
)

API_KEY = os.getenv("FLOWFORGE_API_KEY")

N8N_WEBHOOK_SECRET = os.getenv("N8N_WEBHOOK_SECRET")


# --------------------------------------------------
# API Key Authentication
# --------------------------------------------------

def verify_api_key(
    x_api_key: str | None = Header(default=None),
):
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured",
        )

    if not x_api_key or not secrets.compare_digest(
        x_api_key, API_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


# --------------------------------------------------
# Request Validation Model
# --------------------------------------------------

class CustomerRequest(BaseModel):
    customer_name: str = Field(
        min_length=1,
        max_length=100,
    )

    email: EmailStr

    message: str = Field(
        min_length=1,
        max_length=5000,
    )

    priority: Literal[
        "low",
        "medium",
        "high",
    ] = "medium"


# --------------------------------------------------
# Home Endpoint
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "project": "FlowForge AI",
        "status": "running",
    }


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# --------------------------------------------------
# Customer Request Endpoint
# --------------------------------------------------

@app.post(
    "/requests",
    dependencies=[Depends(verify_api_key)],
)
async def create_request(request: CustomerRequest):

    request_id = str(uuid4())

    payload = {
        "request_id": request_id,
        "customer_name": request.customer_name,
        "email": request.email,
        "message": request.message,
        "priority": request.priority,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    # Verify webhook authentication configuration
    if not N8N_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Webhook authentication is not configured",
        )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:

            response = await client.post(
                N8N_WEBHOOK_URL,
                json=payload,
                headers={
                    "X-FlowForge-Webhook-Secret": (
                        N8N_WEBHOOK_SECRET
                    ),
                },
            )

            response.raise_for_status()

    except httpx.TimeoutException:

        logger.warning(
            "n8n timeout for request_id=%s",
            request_id,
        )

        raise HTTPException(
            status_code=504,
            detail="Automation service timed out",
        ) from None

    except httpx.HTTPError:

        logger.exception(
            "n8n forwarding failed for request_id=%s",
            request_id,
        )

        raise HTTPException(
            status_code=502,
            detail="Automation service is temporarily unavailable",
        ) from None

    return {
        **payload,
        "status": "forwarded_to_n8n",
    }
