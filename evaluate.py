import asyncio
import time
from typing import Literal, NamedTuple

from litellm import acompletion
from pydantic import BaseModel

from src.agent import resolve_dispute
from src.schemas import CustomerDisputeInput, DisputeResolution


class TestCase(BaseModel):
    id: str
    description: str
    request: CustomerDisputeInput
    expected_decision: Literal["REFUND", "VOUCHER", "REQUEST_INFO", "ESCALATE"]
    expected_reasoning_keywords: list[str]


class EvaluationResult(NamedTuple):
    test_id: str
    passed: bool
    latency_ms: float
    decision_match: bool
    reasoning_valid: bool
    obtained_decision: str
    expected_decision: str
    internal_reasoning: str


BENCHMARK_DATASET: list[TestCase] = [
    TestCase(
        id="TC-01",
        description="Atraso severo (>60m) com pedido não entregue",
        request=CustomerDisputeInput(
            order_id="ORD-101",
            customer_id="CUST-001",
            dispute_text="Já se passaram mais de 1 hora e meia do prazo estimado e não recebi minha refeição.",
        ),
        expected_decision="REFUND",
        expected_reasoning_keywords=["atraso", "delay", "severe"],
    ),
    TestCase(
        id="TC-02",
        description="Alegação de falta total de itens sem comprovação",
        request=CustomerDisputeInput(
            order_id="ORD-102",
            customer_id="CUST-099",
            dispute_text="Faltou toda a comida da sacola, exijo estorno integral imediatamente.",
        ),
        expected_decision="ESCALATE",
        expected_reasoning_keywords=["auditoria", "audit", "fraud", "escalat"],
    ),
    TestCase(
        id="TC-03",
        description="Atraso insignificante (<5m) dentro da margem de tolerância",
        request=CustomerDisputeInput(
            order_id="ORD-103",
            customer_id="CUST-023",
            dispute_text="O entregador atrasou 3 minutos em relação à previsão. Quero estorno total.",
        ),
        expected_decision="REQUEST_INFO",
        expected_reasoning_keywords=["tolerância", "tolerance", "minor", "negligible"],
    ),
    TestCase(
        id="TC-04",
        description="Item pontual esquecido (bebida) em refeição composta",
        request=CustomerDisputeInput(
            order_id="ORD-104",
            customer_id="CUST-044",
            dispute_text="A comida chegou perfeita e quente, porém esqueceram o refrigerante de 2L.",
        ),
        expected_decision="VOUCHER",
        expected_reasoning_keywords=["item", "drink", "voucher"],
    ),
    TestCase(
        id="TC-05",
        description="Cancelamento unilateral pelo restaurante parceiro",
        request=CustomerDisputeInput(
            order_id="ORD-105",
            customer_id="CUST-055",
            dispute_text="O restaurante avisou que acabou o estoque e cancelou a preparação do prato.",
        ),
        expected_decision="REFUND",
        expected_reasoning_keywords=["cancelado", "cancel", "out-of-stock"],
    ),
    TestCase(
        id="TC-06",
        description="Dano parcial na embalagem com vazamento de molho",
        request=CustomerDisputeInput(
            order_id="ORD-106",
            customer_id="CUST-061",
            dispute_text="O lanche veio bom, mas o pote de molho especial abriu e sujou o guardanapo.",
        ),
        expected_decision="VOUCHER",
        expected_reasoning_keywords=["compensação", "spill", "voucher", "minor"],
    ),
    TestCase(
        id="TC-07",
        description="Pedido marcado como entregue mas não recebido (auditoria de fraude/GPS)",
        request=CustomerDisputeInput(
            order_id="ORD-107",
            customer_id="CUST-072",
            dispute_text="No aplicativo consta como entregue, mas não há ninguém na minha portaria e não recebi.",
        ),
        expected_decision="ESCALATE",
        expected_reasoning_keywords=["entrega", "audit", "fraud", "mismatch", "delivered"],
    ),
    TestCase(
        id="TC-08",
        description="Pedido entregue com itens trocados e embalagem violada",
        request=CustomerDisputeInput(
            order_id="ORD-108",
            customer_id="CUST-088",
            dispute_text="Veio um prato completamente diferente do que pedi e a embalagem estava rasgada.",
        ),
        expected_decision="ESCALATE",
        expected_reasoning_keywords=["errado", "different", "audit", "severe", "mix-up"],
    ),
    TestCase(
        id="TC-09",
        description="Cliente agressivo com reincidência exigindo supervisor",
        request=CustomerDisputeInput(
            order_id="ORD-109",
            customer_id="CUST-094",
            dispute_text="Já é a quinta vez neste mês que acontece problema. Quero falar com um supervisor agora.",
        ),
        expected_decision="ESCALATE",
        expected_reasoning_keywords=["supervisor", "repeat", "escalat", "human"],
    ),
    TestCase(
        id="TC-10",
        description="Reclamação genérica sem detalhamento",
        request=CustomerDisputeInput(
            order_id="ORD-110",
            customer_id="CUST-030",
            dispute_text="Não gostei do meu pedido, resolvam isso.",
        ),
        expected_decision="REQUEST_INFO",
        expected_reasoning_keywords=["informações", "info", "vague", "detail"],
    ),
]


async def judge_reasoning_quality(agent_reasoning: str, keywords: list[str]) -> bool:
    # Checagem léxica rápida (bilíngue) para economizar tokens e contornar rate limit
    reasoning_lower = agent_reasoning.lower()
    if any(k.lower() in reasoning_lower for k in keywords):
        return True

    # Avaliação LLM apenas se a busca por palavra-chave falhar
    prompt = f"""
    Atue como um auditor técnico. Avalie se a justificativa cobre ao menos um dos seguintes conceitos: {keywords}.
    Justificativa: "{agent_reasoning}"
    Responda apenas TRUE ou FALSE.
    """
    try:
        response = await acompletion(
            model="groq/qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        content = response.choices[0].message.content or ""
        return "TRUE" in content.strip().upper()
    except Exception:
        return False


async def evaluate_single_case(
    test: TestCase, semaphore: asyncio.Semaphore
) -> EvaluationResult:
    async with semaphore:
        start_time = time.perf_counter()
        resolution = None
        max_retries = 5

        for attempt in range(max_retries):
            try:
                resolution = await asyncio.to_thread(resolve_dispute, test.request)
                break
            except Exception as e:
                err_msg = str(e).lower()
                if "429" in err_msg or "rate_limit" in err_msg:
                    wait_time = 4.0 * (attempt + 1)
                    print(f"  [Rate Limit] Aguardando {wait_time}s para retentar {test.id}...")
                    await asyncio.sleep(wait_time)
                else:
                    raise e

        if resolution is None:
            raise RuntimeError(f"Falha por Rate Limit após {max_retries} tentativas em {test.id}")

        latency_ms = (time.perf_counter() - start_time) * 1000

        decision_match = resolution.decision == test.expected_decision
        reasoning_valid = await judge_reasoning_quality(
            resolution.internal_reasoning, test.expected_reasoning_keywords
        )

        passed = decision_match and reasoning_valid

        return EvaluationResult(
            test_id=test.id,
            passed=passed,
            latency_ms=latency_ms,
            decision_match=decision_match,
            reasoning_valid=reasoning_valid,
            obtained_decision=resolution.decision,
            expected_decision=test.expected_decision,
            internal_reasoning=resolution.internal_reasoning,
        )


async def run_benchmark() -> None:
    semaphore = asyncio.Semaphore(1)

    print("=" * 70)
    print("INICIANDO BENCHMARK CONCORRENTE: DISPUTEGUARD (LLM-AS-A-JUDGE)")
    print("=" * 70)

    start_benchmark = time.perf_counter()
    tasks = [evaluate_single_case(test, semaphore) for test in BENCHMARK_DATASET]
    results: list[EvaluationResult] = await asyncio.gather(*tasks)
    total_time_ms = (time.perf_counter() - start_benchmark) * 1000

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.test_id} | Latência: {r.latency_ms:.2f}ms")
        print(f"       Decisão Esperada: {r.expected_decision} | Obtida: {r.obtained_decision}")
        if not r.passed:
            print(f"       Justificativa Interna: {r.internal_reasoning}")

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
