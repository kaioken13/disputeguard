from fastapi import FastAPI, HTTPException

from src.agent import resolve_dispute
from src.schemas import CustomerDisputeInput, DisputeResolution


app = FastAPI(
    title="DisputeGuard API",
    description="Motor autônomo de resolução de disputas do iFood",
)


@app.post("/disputes/resolve", response_model=DisputeResolution)
async def handle_dispute(dispute: CustomerDisputeInput) -> DisputeResolution:
    try:
        # Se resolve_dispute for síncrono, execute diretamente:
        decision = resolve_dispute(dispute)
        return decision
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc