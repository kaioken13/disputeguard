from src.schemas import CustomerDisputeInput, DisputeResolution


def test_customer_dispute_input_valid() -> None:
    data = {
        "order_id": "ORD-12345",
        "customer_id": "CUST-999",
        "dispute_text": "Pedido atrasou mais de 1 hora.",
    }
    dispute = CustomerDisputeInput(**data)
    assert dispute.order_id == "ORD-12345"
    assert dispute.customer_id == "CUST-999"
    assert dispute.dispute_text == "Pedido atrasou mais de 1 hora."


def test_dispute_resolution_schema_valid() -> None:
    resolution = DisputeResolution(
        decision="REFUND",
        customer_response="Seu reembolso foi processado devido ao atraso excessivo.",
        internal_reasoning="Atraso superior a 60 minutos validado pelos dados de GPS do entregador.",
        refund_amount=45.50,
        voucher_amount=10.0,
        confidence_score=0.95,
    )
    assert resolution.decision == "REFUND"
    assert resolution.refund_amount == 45.50
    assert resolution.confidence_score == 0.95
