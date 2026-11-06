import json
from pathlib import Path
from typing import Any

from src.config import settings


def load_order_details(order_id: str) -> dict[str, Any] | None:
    # Tenta o caminho configurado ou busca na raiz caso seja relativo
    path = Path(settings.MOCK_ORDERS_PATH)
    if not path.is_file():
        # Fallback para caso o arquivo esteja na raiz do repositório
        path = Path(__file__).resolve().parent.parent.parent / "mock_orders.json"
        if not path.is_file():
            return None

    try:
        with open(path, encoding="utf-8") as f:
            orders = json.load(f)
        return next((item for item in orders if item.get("order_id") == order_id), None)
    except Exception:
        return None
