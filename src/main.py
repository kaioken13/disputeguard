from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.config import settings
from src.services.resolver import resolve_dispute_pipeline


app = FastAPI(title=settings.PROJECT_NAME)


class DisputeRequest(BaseModel):
    order_id: str
    customer_id: str
    dispute_text: str


@app.get("/health")
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}


@app.post("/v1/disputes/resolve")
async def resolve_dispute(payload: DisputeRequest):
    try:
        result = await resolve_dispute_pipeline(
            order_id=payload.order_id,
            customer_id=payload.customer_id,
            dispute_text=payload.dispute_text,
            vector_context="Atrasos superiores a 45 minutos dão direito a reembolso total imediato.",
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
