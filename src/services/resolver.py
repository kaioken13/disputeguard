import json
import litellm
from src.config import settings
from src.services.order_service import load_order_details


async def resolve_dispute_pipeline(order_id: str, customer_id: str, dispute_text: str, vector_context: str) -> dict:
    order_data = load_order_details(order_id)
    
    if order_data:
        order_summary = (
            f"- Status do Pedido: {order_data.get('order_status')}\n"
            f"- Atraso Registrado: {order_data.get('delay_minutes')} minutos\n"
            f"- Situação do Entregador: {order_data.get('courier_status')}\n"
            f"- Reembolsos Anteriores: {order_data.get('customer_refund_history_count', 0)}\n"
            f"- Valor Total: R$ {order_data.get('order_amount_brl')}"
        )
    else:
        order_summary = "Dados transacionais do pedido não localizados na base operacional."

    prompt = f"""
Você é o motor de governança e resolução de disputas DisputeGuard.
Analise a disputa do cliente confrontando os dados operacionais do pedido e as políticas da plataforma.

POLÍTICAS APLICÁVEIS:
{vector_context}

DADOS TRANSACIONAIS DO PEDIDO:
{order_summary}

RECLAMAÇÃO DO CLIENTE:
"{dispute_text}"

Diretrizes de Decisão:
1. Se houver atraso severo comprovado (> 45 min) ou falha logística, decida por REFUND.
2. Se houver histórico recorrente de reembolsos ou inconsistência grave, decida por ESCALATE.
3. Se o pedido foi entregue no prazo e em conformidade, decida por REJECT.

Responda EXCLUSIVAMENTE em formato JSON com as chaves:
- "decision": "REFUND" | "REJECT" | "ESCALATE"
- "confidence_score": float entre 0.0 e 1.0
- "reasoning": "Explicação sucinta baseada nos dados do pedido e nas políticas"
"""

    response = await litellm.acompletion(
        model=settings.LLM_MODEL,
        api_key=settings.GROQ_API_KEY,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1
    )

    return json.loads(response.choices[0].message.content)
