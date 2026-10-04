"""Home-screen catalogue. Each bill's rules live in its own package."""

from __future__ import annotations

BILLS = (
    {"id": "ultratech", "name": "UltraTech Bill", "available": True},
    {"id": "dalmia-lalan", "name": "Dalmia Bill – Lalan", "available": True},
    {"id": "dalmia-shila", "name": "Dalmia Bill – Shila", "available": True},
    {"id": "acc-lalan", "name": "ACC Bill – Lalan", "available": True},
    {"id": "acc-shila", "name": "ACC Bill – Shila", "available": True},
)


def list_bills() -> list[dict[str, object]]:
    return [dict(item) for item in BILLS]
