from fastapi import FastAPI, HTTPException
from src.schemas import CustomerDisputeInput, DisputeResolution
from src.agent import resolve_dispute

app = FastAPI(
    title="DisputeGuard AI",
    version="1.0.0",
    description="Agente autônomo de resolução de disputas de e-commerce e delivery."
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "disputeguard"}

@app.post("/api/v1/dispute/resolve", response_model=DisputeResolution)
async def process_dispute(payload: CustomerDisputeInput):
    try:
        decision = resolve_dispute(payload)
        return decision
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))