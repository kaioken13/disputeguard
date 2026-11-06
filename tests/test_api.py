from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.main import app
from src.schemas import DisputeResolution


client = TestClient(app)


def test_resolve_dispute_endpoint_success() -> None:
    mock_resolution = DisputeResolution(
        decision="REFUND",
        customer_response="Seu reembolso foi processado com sucesso devido ao atraso comprovado.",
        internal_reasoning="Atraso superior a 60 minutos confirmado pela telemetria do entregador.",
        confidence_score=0.98,
    )

    payload = {
        "order_id": "ORD-98765",
        "customer_id": "CUST-1234",
        "dispute_text": "O entregador demorou mais de 70 minutos e a comida chegou totalmente fria.",
    }

    with patch(
        "src.main.resolve_dispute_pipeline", new_callable=AsyncMock
    ) as mock_pipeline:
        mock_pipeline.return_value = mock_resolution

        response = client.post("/v1/disputes/resolve", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "REFUND"
        assert data["confidence_score"] == 0.98
        assert "Atraso superior a 60 minutos" in data["internal_reasoning"]
