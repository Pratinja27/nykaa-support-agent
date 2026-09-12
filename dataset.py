import json
import random
from collections import Counter

# Generator Parameters
SEED = 42
NUM_RECORDS = 50

# Price range reasoning: Reflects Nykaa's retail spectrum spanning budget personal care items (₹299) up to high-end beauty devices and luxury apparel sets (₹25,000).
MIN_ORDER_VALUE = 299
MAX_ORDER_VALUE = 25000

CATEGORIES = ["Apparel", "Electronics", "Home", "Footwear", "Beauty"]
CATEGORY_WEIGHTS = [0.20, 0.20, 0.20, 0.20, 0.20]

STATUSES = ["Placed", "Shipped", "Delivered", "Returned", "Refunded"]
STATUS_WEIGHTS = [0.20, 0.25, 0.35, 0.10, 0.10]

TARGET_DELAY_PROB = 0.18


def build_order_records(seed_val: int):
    random.seed(seed_val)
    records = []

    for idx in range(NUM_RECORDS):
        cat = random.choices(CATEGORIES, weights=CATEGORY_WEIGHTS, k=1)[0]
        stat = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        val = random.randint(MIN_ORDER_VALUE, MAX_ORDER_VALUE)
        recency = random.randint(0, 30)
        is_delayed = random.random() < TARGET_DELAY_PROB

        records.append({
            "record_id": f"ORD{1001 + idx}",
            "category": cat,
            "status": stat,
            "order_value_inr": val,
            "days_since_created": recency,
            "delayed_shipment": is_delayed
        })

    return records


def audit_dataset(records):
    cat_counts = Counter(r["category"] for r in records)
    stat_counts = Counter(r["status"] for r in records)
    delayed_total = sum(1 for r in records if r["delayed_shipment"])
    delay_pct = (delayed_total / len(records)) * 100

    # Task 1 constraints validation
    if len(records) < 40:
        return False, "Record count below 40"

    for c in CATEGORIES:
        if cat_counts[c] < 3:
            return False, f"Category {c} has under 3 entries"

    for s in STATUSES:
        if stat_counts[s] < 1:
            return False, f"Missing status {s}"

    if not (10.0 <= delay_pct <= 30.0):
        return False, f"Delay percentage {delay_pct:.1f}% outside 10-30% bounds"

    return True, "OK"


def generate_valid_dataset(start_seed=SEED):
    curr_seed = start_seed
    while True:
        orders = build_order_records(curr_seed)
        valid, msg = audit_dataset(orders)
        if valid:
            return orders, curr_seed
        # Auto-calibrate seed if target delay bounds fail (Rubric Task 1 mandate)
        curr_seed += 1


ORDERS, FINAL_SEED = generate_valid_dataset()

# Export for agent usage
with open("data/orders.json", "w", encoding="utf-8") as f:
    json.dump(ORDERS, f, indent=2)


if __name__ == "__main__":
    cat_summary = Counter(o["category"] for o in ORDERS)
    stat_summary = Counter(o["status"] for o in ORDERS)
    delayed_count = sum(1 for o in ORDERS if o["delayed_shipment"])
    pct = (delayed_count / len(ORDERS)) * 100

    print("--- NYKAA DATASET SUMMARY ---")
    print(f"Seed used: {FINAL_SEED}")
    print(f"Total records generated: {len(ORDERS)}")
    print(f"Category breakdown: {dict(cat_summary)}")
    print(f"Status breakdown: {dict(stat_summary)}")
    print(f"Delayed shipments: {delayed_count}/{len(ORDERS)} ({pct:.2f}%)")
    print(f"Price range: ₹{MIN_ORDER_VALUE} - ₹{MAX_ORDER_VALUE}")
    print("----------------------------")