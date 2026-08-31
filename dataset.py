import random
import json
from collections import Counter


SEED = 42
NUM_RECORDS = 50

CATEGORIES = [
    "Apparel",
    "Electronics",
    "Home",
    "Footwear",
    "Beauty"
]

STATUSES = [
    "Placed",
    "Shipped",
    "Delivered",
    "Returned",
    "Refunded"
]

CATEGORY_WEIGHTS = [0.20, 0.20, 0.20, 0.20, 0.20]

STATUS_WEIGHTS = [0.20, 0.25, 0.35, 0.10, 0.10]

MIN_ORDER_VALUE = 299
MAX_ORDER_VALUE = 25000

DELAY_PROBABILITY = 0.20


def generate_orders():
    random.seed(SEED)

    orders = []

    for i in range(NUM_RECORDS):
        order = {
            "record_id": f"ORD{1001 + i}",
            "category": random.choices(
                CATEGORIES,
                weights=CATEGORY_WEIGHTS,
                k=1
            )[0],
            "status": random.choices(
                STATUSES,
                weights=STATUS_WEIGHTS,
                k=1
            )[0],
            "order_value_inr": random.randint(
                MIN_ORDER_VALUE,
                MAX_ORDER_VALUE
            ),
            "days_since_created": random.randint(0, 30),
            "delayed_shipment": random.random() < DELAY_PROBABILITY
        }

        orders.append(order)

    return orders


def validate_dataset(orders):
    errors = []

    if len(orders) < 40:
        errors.append("At least 40 records are required.")

    category_counts = Counter(
        order["category"] for order in orders
    )

    for category in CATEGORIES:
        if category_counts[category] < 3:
            errors.append(
                f"{category} has fewer than 3 records."
            )

    status_counts = Counter(
        order["status"] for order in orders
    )

    for status in STATUSES:
        if status_counts[status] < 1:
            errors.append(
                f"{status} does not appear in the dataset."
            )

    for order in orders:
        if not MIN_ORDER_VALUE <= order["order_value_inr"] <= MAX_ORDER_VALUE:
            errors.append(
                f"{order['record_id']} has an invalid order value."
            )

        if not 0 <= order["days_since_created"] <= 30:
            errors.append(
                f"{order['record_id']} has an invalid age."
            )

        if not isinstance(order["delayed_shipment"], bool):
            errors.append(
                f"{order['record_id']} has an invalid delayed shipment value."
            )

    delayed_count = sum(
        order["delayed_shipment"] for order in orders
    )

    delayed_percentage = (delayed_count / len(orders)) * 100

    if not 10 <= delayed_percentage <= 30:
        errors.append(
            f"Delayed shipment percentage is "
            f"{delayed_percentage:.2f}%, outside the required range."
        )

    return errors


def print_report(orders):
    category_counts = Counter(
        order["category"] for order in orders
    )

    status_counts = Counter(
        order["status"] for order in orders
    )

    delayed_count = sum(
        order["delayed_shipment"] for order in orders
    )

    delayed_percentage = (delayed_count / len(orders)) * 100

    print("=" * 50)
    print("NYKAA ORDER DATASET REPORT")
    print("=" * 50)

    print(f"Seed: {SEED}")
    print(f"Total records: {len(orders)}")

    print("\nCategory counts:")
    for category in CATEGORIES:
        print(f"{category}: {category_counts[category]}")

    print("\nStatus counts:")
    for status in STATUSES:
        print(f"{status}: {status_counts[status]}")

    print("\nDelayed shipments:")
    print(
        f"{delayed_count}/{len(orders)} "
        f"({delayed_percentage:.2f}%)"
    )

    errors = validate_dataset(orders)

    print("\nValidation:")

    if not errors:
        print("Dataset satisfies all Task 1 requirements.")
    else:
        for error in errors:
            print(error)

    print("=" * 50)

def save_orders(orders):
    with open("data/orders.json", "w", encoding="utf-8") as file:
        json.dump(orders, file, indent=2)


ORDERS = generate_orders()
save_orders(ORDERS)

if __name__ == "__main__":
    print_report(ORDERS)