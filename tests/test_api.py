from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_resolve_dispute_endpoint_success() -> None:
    payload = {
        "order_id": "ORD-98765",
        "customer_id": "CUST-1234",
        "dispute_text": "O entregador demorou mais de 70 minutos e a comida chegou totalmente fria.",
    }

    response = client.post("/v1/disputes/resolve", json=payload)

    assert response.status_code == 200
    data = response.json()

    # Validação do contrato público retornado pelo endpoint
    assert data["decision"] in ["REFUND", "VOUCHER", "REQUEST_INFO", "ESCALATE"]
    assert data["decision"] == "REFUND"
    assert 0.0 <= data["confidence_score"] <= 1.0
    assert "reasoning" in data
    assert isinstance(data["reasoning"], str)
    assert len(data["reasoning"]) > 0
