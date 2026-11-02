from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions


chroma_client = chromadb.Client()

policy_collection = chroma_client.get_or_create_collection(
    name="policies",
    embedding_function=embedding_functions.DefaultEmbeddingFunction(),  # type: ignore[arg-type]
)

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
# Na inicialização da collection (linha 50):
# Use cast(Any, ...) ou type: ignore[arg-type] para neutralizar o stub imperfeito do ChromaDB:
policy_collection = chroma_client.get_or_create_collection(
    name="policies",
    policy_collection = chroma_client.get_or_create_collection(name="policies"),
)

# Na função search_policy (linha 70):
# Valide se documents existe e não é None antes de indexar:
def search_policy(query: str, n_results: int = 2) -> list[str]:
    """Recupera as cláusulas de reembolso mais relevantes baseadas no relato da disputa."""
    results = policy_collection.query(query_texts=[query], n_results=n_results)

    docs = results.get("documents")
    if docs and len(docs) > 0 and docs[0] is not None:
        return docs[0]
    return []
