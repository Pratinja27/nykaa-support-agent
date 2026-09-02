import json
import os
from pathlib import Path
from typing import List, Dict


MEMORY_FILE = Path(__file__).parent / "memory.json"


def _load_all() -> Dict[str, List[Dict[str, str]]]:
    if not os.path.exists(MEMORY_FILE):
        return {}

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save_all(data: Dict[str, List[Dict[str, str]]]) -> None:
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_memory(thread_id: str) -> List[Dict[str, str]]:
    """Return the message history for a given thread_id (empty list if none)."""
    data = _load_all()
    return data.get(thread_id, [])


def add_message(thread_id: str, role: str, content: str) -> None:
    """Append a message to a thread's history and persist it."""
    data = _load_all()

    if thread_id not in data:
        data[thread_id] = []

    data[thread_id].append({
        "role": role,
        "content": content
    })

    _save_all(data)


def clear_thread(thread_id: str) -> None:
    """Remove a thread's history entirely. Useful before clean test runs."""
    data = _load_all()

    if thread_id in data:
        del data[thread_id]
        _save_all(data)


if __name__ == "__main__":
    # Quick manual test
    clear_thread("thread_test")

    add_message("thread_test", "user", "My order is ORD1001")
    add_message("thread_test", "assistant", "Order ORD1001 is currently Placed...")

    print(load_memory("thread_test"))