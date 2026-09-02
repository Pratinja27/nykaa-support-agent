from dataset import ORDERS


ESCALATION_THRESHOLD = 0.75


def get_recency_percentile(percentile):
    days = sorted(
        order["days_since_created"]
        for order in ORDERS
    )

    index = int(
        (percentile / 100) * (len(days) - 1)
    )

    return days[index]


def check_order_status(record_id: str) -> dict:
    order = next(
        (
            item
            for item in ORDERS
            if item["record_id"] == record_id
        ),
        None
    )

    if order is None:
        raise ValueError(
            f"Order {record_id} not found"
        )

    recency_score = (
        order["days_since_created"] / 30
    )

    delayed_signal = (
        1.0 if order["delayed_shipment"] else 0.0
    )

    escalation_score = (
        0.6 * delayed_signal
        + 0.4 * recency_score
    )

    return {
        "record_id": order["record_id"],
        "status": order["status"],
        "order_value_inr": order["order_value_inr"],
        "escalation_score": round(
            escalation_score,
            3
        ),
        "escalation_recommended": (
            escalation_score >= ESCALATION_THRESHOLD
        )
    }


if __name__ == "__main__":
    print("TASK 6 - ORDER STATUS TOOL")
    print("=" * 60)

    print("\nESCALATION CONFIGURATION")
    print(f"Formula: 0.6 × delayed_signal + 0.4 × recency_score")
    print(f"Recency score: days_since_created / 30")
    print(f"Escalation threshold: {ESCALATION_THRESHOLD}")
    print("80th percentile of days_since_created: "
          f"{get_recency_percentile(80)} days")

    print("\nHIGH ESCALATION ORDER")
    print("=" * 60)

    high_found = False

    for order in ORDERS:
        result = check_order_status(
            order["record_id"]
        )

        if result["escalation_recommended"]:
            print(result)
            high_found = True
            break

    if not high_found:
        print("No order crossed the escalation threshold.")

    print("\nLOW ESCALATION ORDER")
    print("=" * 60)

    for order in ORDERS:
        result = check_order_status(
            order["record_id"]
        )

        if not result["escalation_recommended"]:
            print(result)
            break

    print("\nDIRECT LOOKUP TEST")
    print("=" * 60)

    test_id = ORDERS[0]["record_id"]

    print(
        f"Checking record ID: {test_id}"
    )

    print(
        check_order_status(test_id)
    )