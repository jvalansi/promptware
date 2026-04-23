import json
from pathlib import Path

CUSTOMERS_FILE = Path(__file__).parent.parent / "customers.json"


def get_customer(api_key: str) -> dict | None:
    if not CUSTOMERS_FILE.exists():
        return None
    customers = json.loads(CUSTOMERS_FILE.read_text())
    return customers.get(api_key)
