import asyncio
import time
from typing import NamedTuple

from litellm import acompletion
from pydantic import BaseModel

from src.agent import DisputeAgent
from src.schemas import ActionType, DisputeDecision, DisputeRequest


class TestCase(BaseModel):
    id: str
    description: str
    request: DisputeRequest
    expected_action: ActionType
    expected_reasoning_keyword: str


class EvaluationResult(NamedTuple):
    test_id: str
    passed: bool
    latency_ms: float
    action_match: bool
    reasoning_valid: bool
    obtained_action: str
    expected_action: str
    reasoning: str


BENCHMARK_DATASET: list[TestCase] = [
    TestCase(
        id="TC-01",
        description="Atraso extremo de entrega (>60m) com GPS confirmando entregador longe",
        request=DisputeRequest(
            order_id="ORD-101",
            customer_id="CUST-001",
            issue_type="late_delivery",
            customer_comment="Já passou 1h30 do prazo e o entregador nem se move no mapa.",
            driver_distance_km=8.5,
            delivery_delay_minutes=75,
            dispute_history_count=0,
        ),
        expected_action=ActionType.REFUND,
        expected_reasoning_keyword="atraso",
    ),
    TestCase(
        id="TC-02",
        description="Cliente com alto volume de contestações prévias e sem evidência concreta",
        request=DisputeRequest(
            order_id="ORD-102",
            customer_id="CUST-099",
            issue_type="missing_items",
            customer_comment="Faltou toda a comida, exijo reembolso total agora.",
            driver_distance_km=0.05,
            delivery_delay_minutes=0,
            dispute_history_count=8,
        ),
        expected_action=ActionType.ESCALATE_HUMAN,
        expected_reasoning_keyword="histórico",
    ),
    TestCase(
        id="TC-03",
        description="Pedido entregue no raio de precisão com atraso desprezível (<5 min)",
        request=DisputeRequest(
            order_id="ORD-103",
            customer_id="CUST-023",
            issue_type="late_delivery",
            customer_comment="Atrasou 3 minutos, quero cancelar e ter meu dinheiro de volta.",
            driver_distance_km=0.02,
            delivery_delay_minutes=3,
            dispute_history_count=1,
        ),
        expected_action=ActionType.DENY,
        expected_reasoning_keyword="tolerância",
    ),
]


async def judge_reasoning_quality(agent_reasoning: str, expected_keyword: str) -> bool:
    prompt = f"""
    Atue como um auditor rigoroso de suporte e compliance para delivery.
    Avalie a justificativa técnica gerada pelo agente de IA.

    Justificativa do Agente: "{agent_reasoning}"
    Conceito Obrigatório Esperado: "{expected_keyword}"

    A justificativa faz sentido técnico e cobre a essência do conceito esperado?
    Responda apenas com 'TRUE' ou 'FALSE'.
    """
    try:
        response = await acompletion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        content = response.choices[0].message.content or ""
        return "TRUE" in content.strip().upper()
    except Exception:
        # Fallback semântico determinístico
        return expected_keyword.lower() in agent_reasoning.lower()


async def evaluate_single_case(
    test: TestCase, agent: DisputeAgent, semaphore: asyncio.Semaphore
) -> EvaluationResult:
    async with semaphore:
        start_time = time.perf_counter()
        decision: DisputeDecision = await agent.evaluate_dispute(test.request)
        latency_ms = (time.perf_counter() - start_time) * 1000

        action_match = decision.action == test.expected_action
        reasoning_valid = await judge_reasoning_quality(
            decision.reasoning, test.expected_reasoning_keyword
        )

        passed = action_match and reasoning_valid

        return EvaluationResult(
            test_id=test.id,
            passed=passed,
            latency_ms=latency_ms,
            action_match=action_match,
            reasoning_valid=reasoning_valid,
            obtained_action=decision.action.value,
            expected_action=test.expected_action.value,
            reasoning=decision.reasoning,
        )


async def run_benchmark() -> None:
    agent = DisputeAgent()
    semaphore = asyncio.Semaphore(5)  # Limita concorrência para evitar rate limits

    print("=" * 70)
    print("INICIANDO BENCHMARK CONCORRENTE: DISPUTEGUARD (LLM-AS-A-JUDGE)")
    print("=" * 70)

    start_benchmark = time.perf_counter()
    tasks = [evaluate_single_case(test, agent, semaphore) for test in BENCHMARK_DATASET]
    results: list[EvaluationResult] = await asyncio.gather(*tasks)
    total_time_ms = (time.perf_counter() - start_benchmark) * 1000

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.test_id} | Latência: {r.latency_ms:.2f}ms")
        print(f"       Ação Esperada: {r.expected_action} | Obtida: {r.obtained_action}")
        if not r.passed:
            print(f"       Justificativa: {r.reasoning}")

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    accuracy = (passed_tests / total_tests) * 100
    latencies = sorted([r.latency_ms for r in results])
    avg_latency = sum(latencies) / len(latencies)
    p95_index = min(int(len(latencies) * 0.95), len(latencies) - 1)
    p95_latency = latencies[p95_index]

    print("\n" + "-" * 70)
    print("RELATÓRIO CONSOLIDADO DE PERFORMANCE E GOVERNANÇA")
    print("-" * 70)
    print(f"Acurácia Global:      {accuracy:.1f}% ({passed_tests}/{total_tests})")
    print(f"Tempo Total do Batch: {total_time_ms:.2f} ms")
    print(f"Latência Média:       {avg_latency:.2f} ms")
    print(f"Latência P95:         {p95_latency:.2f} ms")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_benchmark())
