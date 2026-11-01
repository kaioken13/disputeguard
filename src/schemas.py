from typing import Literal, Optional
from pydantic import BaseModel, Field

class CustomerDisputeInput(BaseModel):
    order_id: str = Field(..., description="Identificador único do pedido, ex: ORD-1042")
    customer_id: str = Field(..., description="ID do usuário reclamante")
    dispute_text: str = Field(..., description="Relato do problema enviado pelo cliente")

class OrderItem(BaseModel):
    name: str
    price: float
    quantity: int

class OrderDetails(BaseModel):
    order_id: str
    customer_id: str
    restaurant_name: str
    items: list[OrderItem]
    total_amount: float
    delivery_status: str
    promised_delivery_time_min: int
    actual_delivery_time_min: int
    customer_dispute_rate_last_10: float

class DisputeResolution(BaseModel):
    decision: Literal["REFUND", "VOUCHER", "REQUEST_INFO", "ESCALATE"] = Field(
        ..., description="Ação autônoma executada pelo agente"
    )
    refund_amount: Optional[float] = Field(
        default=0.0, description="Valor a ser estornado caso a decisão seja REFUND"
    )
    voucher_amount: Optional[float] = Field(
        default=0.0, description="Valor do voucher compensatório caso aplicável"
    )
    customer_response: str = Field(
        ..., description="Mensagem em tom empático, direto e profissional para o cliente final"
    )
    internal_reasoning: str = Field(
        ..., description="Justificativa técnica da decisão com base nas políticas e dados do pedido"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Grau de certeza do agente sobre a decisão aplicada"
    )