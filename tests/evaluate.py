import asyncio
import time

from litellm import acompletion
from pydantic import BaseModel

from app.agent import DisputeAgent
from app.schemas import ActionType, DisputeDecision, DisputeRequest


class TestCase(BaseModel):
    id: str
    description: str
    request: DisputeRequest
    expected_action: ActionType
    expected_reasoning_keyword: str


# 1. Dataset de Benchmark Sintético com Casos de Borda Reais de Delivery
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


# 2. Avaliador LLM-as-a-Judge
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
    except (RuntimeError, ValueError, KeyError):
        # Fallback determinístico caso a API do judge oscile
        return expected_keyword.lower() in agent_reasoning.lower()


# 3. Pipeline de Execução de Benchmark
async def run_benchmark() -> None:
    agent = DisputeAgent()
    results: list[bool] = []
    latencies: list[float] = []

    print("=" * 60)
    print("INICIANDO BENCHMARK DE PRODUÇÃO: DISPUTEGUARD (LLM-AS-A-JUDGE)")
    print("=" * 60)

    for test in BENCHMARK_DATASET:
        start_time = time.perf_counter()

        # Execução do agente
        decision: DisputeDecision = await agent.evaluate_dispute(test.request)

        latency = (time.perf_counter() - start_time) * 1000
        latencies.append(latency)

        # Validação de Acurácia de Decisão
        action_match = decision.action == test.expected_action

        # Avaliação semântica via LLM-as-a-judge
        reasoning_valid = await judge_reasoning_quality(
            decision.reasoning,
            test.expected_reasoning_keyword,
        )

        passed = action_match and reasoning_valid
        results.append(passed)

        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test.id}: {test.description}")
        print(
            f"       Latência: {latency:.2f}ms | Ação Esperada: {test.expected_action.value} | Ação Obtida: {decision.action.value}"
        )
        if not passed:
            print(f"       Justificativa: {decision.reasoning}")

    # 4. Cálculo de Métricas Finais
    total_tests = len(BENCHMARK_DATASET)
    passed_tests = sum(results)
    accuracy = (passed_tests / total_tests) * 100
    avg_latency = sum(latencies) / len(latencies)
    latencies.sort()
    p95_latency = latencies[int(len(latencies) * 0.95)]

    print("\n" + "-" * 60)
    print("RELATÓRIO CONSOLIDADO DE PERFORMANCE E GOVERNANÇA")
    print("-" * 60)
    print(f"Acurácia Global de Decisão: {accuracy:.1f}% ({passed_tests}/{total_tests})")
    print(f"Latência Média:             {avg_latency:.2f} ms")
    print(f"Latência P95:               {p95_latency:.2f} ms")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_benchmark())
