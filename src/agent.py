import re

from litellm import completion

from src.schemas import CustomerDisputeInput, DisputeResolution


SYSTEM_PROMPT = """You are an autonomous AI dispute agent. You must respond ONLY with a valid JSON object.
Do not write explanations outside the JSON.

Required schema:
{
  "decision": "REFUND" | "VOUCHER" | "REQUEST_INFO" | "ESCALATE",
  "refund_amount": 0.0,
  "voucher_amount": 0.0,
  "customer_response": "Empathetic and professional response to the customer",
  "internal_reasoning": "Technical justification explaining delay, audit, history, or tolerance",
  "confidence_score": 0.95
}

Decision Rules:
- ESCALATE: Missing entire order, suspected fraud, repeat disputes, or requiring human audit.
- REFUND: Severe delay (>45m), cancelled by restaurant, or confirmed non-delivery.
- VOUCHER: Single missing secondary item (e.g., drink) or minor spill.
- REQUEST_INFO: Negligible delay (<5m within tolerance) or vague complaint lacking details.
"""


def resolve_dispute(input_data: CustomerDisputeInput) -> DisputeResolution:
    model = "groq/qwen/qwen3.8-27b"

    user_message = (
        f"Order ID: {input_data.order_id}\n"
        f"Customer ID: {input_data.customer_id}\n"
        f"Dispute: {input_data.dispute_text}\n\n"
        "Generate the dispute resolution JSON:"
    )

    response = completion(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    raw_content = response.choices[0].message.content.strip()

    json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
    if json_match:
        raw_content = json_match.group(0)

    return DisputeResolution.model_validate_json(raw_content)
