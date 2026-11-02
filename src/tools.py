from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions


# 1. Base Mock de Pedidos
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MOCK_ORDERS = {
    "ORD-101": {
        "order_id": "ORD-101",
        "customer_id": "USER-99",
        "restaurant_name": "Hamburgueria Brasa Burguer",
        "items": [
            {"name": "X-Bacon Smash", "price": 38.00, "quantity": 1},
            {"name": "Batata Rústica", "price": 18.00, "quantity": 1},
            {"name": "Refrigerante Lata", "price": 7.00, "quantity": 1},
        ],
        "total_amount": 63.00,
        "delivery_status": "DELIVERED",
        "promised_delivery_time_min": 35,
        "actual_delivery_time_min": 78,
        "customer_dispute_rate_last_10": 0.10,
    },
    "ORD-102": {
        "order_id": "ORD-102",
        "customer_id": "USER-42",
        "restaurant_name": "Sushi Express",
        "items": [{"name": "Combo Salmão 20 peças", "price": 89.00, "quantity": 1}],
        "total_amount": 89.00,
        "delivery_status": "DELIVERED",
        "promised_delivery_time_min": 40,
        "actual_delivery_time_min": 42,
        "customer_dispute_rate_last_10": 0.60,  # Taxa alta de disputa: suspeita de fraude
    },
}


def get_order_details(order_id: str) -> dict:
    """Consulta o banco de dados e retorna os metadados do pedido e histórico do cliente."""
    if order_id not in MOCK_ORDERS:
        return {"error": f"Pedido {order_id} não encontrado."}
    return MOCK_ORDERS[order_id]


# 2. Inicialização do Vector Store ChromaDB com a Política
chroma_client = chromadb.Client()
emb_fn = embedding_functions.DefaultEmbeddingFunction()
policy_collection = chroma_client.get_or_create_collection(
    name="delivery_policies", embedding_function=emb_fn
)


def setup_policy_index():
    policy_path = DATA_DIR / "delivery_policy.md"
    if not policy_path.exists():
        return
    content = policy_path.read_text(encoding="utf-8")
    sections = [s.strip() for s in content.split("\n\n") if s.strip()]
    ids = [f"policy_rule_{i}" for i in range(len(sections))]
    policy_collection.upsert(documents=sections, ids=ids)


setup_policy_index()


def search_policy(query: str, n_results: int = 2) -> list[str]:
    """Recupera as cláusulas de reembolso mais relevantes baseadas no relato da disputa."""
    results = policy_collection.query(query_texts=[query], n_results=n_results)
    return results["documents"][0] if results and "documents" in results else []
