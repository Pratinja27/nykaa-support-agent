import json
from pathlib import Path

# Tool configurations
DATASET_FILE = Path("data/orders.json")
ESCALATION_CUTOFF = 0.75

# Escalation Weights
WEIGHT_DELAY = 0.60
WEIGHT_RECENCY = 0.40
MAX_RECENCY_DAYS = 30.0


def load_order_dataset():
    """Loads order records dynamically from the local JSON file."""
    if not DATASET_FILE.exists():
        raise FileNotFoundError(f"Orders database missing at {DATASET_FILE}")
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def check_order_status(record_id: str) -> dict:
    """
    Fetches status for a given record ID and computes a composite escalation score.
    
    Formula:
        Score = (0.6 * delayed_flag) + (0.4 * (days_since_created / 30))
    """
    orders = load_order_dataset()
    
    # Locate order by ID (case-insensitive lookup)
    target_id = record_id.strip().upper()
    order = next((o for o in orders if o["record_id"].upper() == target_id), None)

    if order is None:
        return {
            "error": f"Order ID '{record_id}' not found in active database.",
            "found": False
        }

    # Normalize individual signals
    delay_signal = 1.0 if order.get("delayed_shipment", False) else 0.0
    recency_ratio = min(order.get("days_since_created", 0) / MAX_RECENCY_DAYS, 1.0)

    # Calculate weighted composite escalation score (0.0 to 1.0 scale)
    composite_score = (WEIGHT_DELAY * delay_signal) + (WEIGHT_RECENCY * recency_ratio)
    composite_score = round(composite_score, 3)

    return {
        "found": True,
        "record_id": order["record_id"],
        "status": order["status"],
        "category": order["category"],
        "order_value_inr": order["order_value_inr"],
        "days_since_created": order["days_since_created"],
        "delayed_shipment": order["delayed_shipment"],
        "escalation_score": composite_score,
        "escalation_recommended": composite_score >= ESCALATION_CUTOFF
    }


def compute_recency_percentile(orders, percentile=80):
    """Calculates percentile distribution for dataset recency."""
    ages = sorted(o["days_since_created"] for o in orders)
    idx = int((percentile / 100.0) * (len(ages) - 1))
    return ages[idx]


if __name__ == "__main__":
    print("=== TASK 6: ORDER TOOL & ESCALATION SCORE AUDIT ===")
    records = load_order_dataset()
    p80_val = compute_recency_percentile(records, 80)
    
    print(f"Total Dataset Records: {len(records)}")
    print(f"80th Percentile Recency: {p80_val} days")
    print(f"Formula: ({WEIGHT_DELAY} * Delay) + ({WEIGHT_RECENCY} * (Days / 30))")
    print(f"Escalation Cutoff: {ESCALATION_CUTOFF}\n")

    # Sample High Escalation
    high_esc = next((check_order_status(o["record_id"]) for o in records 
                     if (WEIGHT_DELAY * (1.0 if o["delayed_shipment"] else 0.0) + WEIGHT_RECENCY * (o["days_since_created"]/30.0)) >= ESCALATION_CUTOFF), None)
    
    print("Sample High-Escalation Payload:")
    print(high_esc)

    # Sample Direct Lookup
    print("\nSample Direct Lookup (ORD1001):")
    print(check_order_status("ORD1001"))