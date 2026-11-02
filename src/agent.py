import json

from litellm import completion

from src.schemas import CustomerDisputeInput, DisputeResolution
from src.tools import get_order_details, search_policy


SYSTEM_PROMPT = """Você é o motor de decisão autônomo do iFood para disputas de pedidos (DisputeGuard).
Sua missão é resolver o problema do cliente de forma justa, aderente às políticas internas e sem alucinar.

Passos obrigatórios:
1. Analise o relato do cliente.
2. Examine os dados reais do pedido (itens, atraso na entrega, histórico de disputas).
3. Avalie as políticas de cancelamento e reembolso recuperadas.
4. Responda ESTRITAMENTE em formato JSON compatível com o schema especificado.
"""


def resolve_dispute(
    dispute: CustomerDisputeInput, model: str = "groq/llama-3.1-70b-versatile"
) -> DisputeResolution:
    # 1. Recupera contexto de infra e políticas
    order_data = get_order_details(dispute.order_id)
    relevant_rules = search_policy(dispute.dispute_text)

    prompt = f"""
    DADOS DO PEDIDO:
    {json.dumps(order_data, indent=2, ensure_ascii=False)}

    POLÍTICAS APLICÁVEIS:
    {json.dumps(relevant_rules, indent=2, ensure_ascii=False)}

    RELATO DO CLIENTE:
    "{dispute.dispute_text}"

    Gere a decisão final estruturada:
    """

    response = completion(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    raw_json = response.choices[0].message.content
    return DisputeResolution.model_validate_json(raw_json)
