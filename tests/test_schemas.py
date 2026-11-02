from src.schemas import ActionType, DisputeDecision, DisputeRequest


def test_dispute_request_schema_valid() -> None:
    req = DisputeRequest(
        order_id="ORD-123",
        customer_id="CUST-456",
        issue_type="late_delivery",
        customer_comment="Demorou muito para chegar",
        driver_distance_km=4.2,
        delivery_delay_minutes=50,
        dispute_history_count=0,
    )
    assert req.order_id == "ORD-123"
    assert req.delivery_delay_minutes == 50


def test_dispute_decision_schema_valid() -> None:
    decision = DisputeDecision(
        action=ActionType.REFUND,
        reasoning="Atraso superior a 45 minutos confirmado pelo rastreio.",
        confidence=0.98,
        eligible_for_voucher=False,
    )
    assert decision.action == ActionType.REFUND
    assert decision.confidence == 0.98
