from fastapi import FastAPI
from src.schemas import CustomerDisputeInput, DisputeResolution
from src.agent import resolve_dispute

app = FastAPI(title="DisputeGuard", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/v1/disputes/resolve", response_model=DisputeResolution)
def handle_dispute(payload: CustomerDisputeInput):
    return resolve_dispute(payload)
