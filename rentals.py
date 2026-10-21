"""Date-only rental rules, independent of HTTP, UI and persistence."""

from datetime import date, datetime, timezone, timedelta
import re


class RentalError(ValueError):
    def __init__(self, message, code="invalid_reservation", status=400):
        super().__init__(message)
        self.code = code
        self.status = status


def today():
    return datetime.now(timezone.utc).date().isoformat()


def calendar(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise RentalError("Choose valid calendar dates.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise RentalError("Choose valid calendar dates.") from None


def period(start, end, asof):
    a, b, now = calendar(start), calendar(end), calendar(asof)
    days = (b - a).days
    if a < now:
        raise RentalError("Collection cannot be before today (UTC).")
    if (a - now).days > 365:
        raise RentalError("Choose collection within the next 365 days.")
    if not 1 <= days <= 365:
        raise RentalError("Return must be 1–365 days after collection.")
    return days


def selection(payload):
    if not isinstance(payload, dict):
        raise RentalError("Provide a reservation object.")
    for key in ["vehicle_id", "customer_id"]:
        if type(payload.get(key)) is not int or not 1 <= payload[key] <= 2147483647:
            raise RentalError("Choose an existing vehicle and customer.")
    return {
        k: payload.get(k)
        for k in ["vehicle_id", "customer_id", "start_date", "end_date"]
    }


def overlaps(row, start, end):
    return (
        row["status"] == "confirmed"
        and row["start_date"] < end
        and start < row["end_date"]
    )


def quote(cars, customers, reservations, payload, asof):
    chosen = selection(payload)
    days = period(chosen["start_date"], chosen["end_date"], asof)
    car = next((c for c in cars if c["id"] == chosen["vehicle_id"]), None)
    customer = next((c for c in customers if c["id"] == chosen["customer_id"]), None)
    if not car or not customer:
        raise RentalError(
            "The selected vehicle or customer no longer exists.", "record_missing", 404
        )
    if any(
        r["vehicle_id"] == car["id"]
        and overlaps(r, chosen["start_date"], chosen["end_date"])
        for r in reservations
    ):
        raise RentalError(
            "This vehicle is already reserved for part of that period. Choose other dates or a different vehicle.",
            "vehicle_unavailable",
            409,
        )
    if type(car["Price"]) is not int or not 0 <= car["Price"] <= 1_000_000_000:
        raise RentalError(
            "This vehicle has an invalid daily rate.", "invalid_rate", 409
        )
    rate = car["Price"] * 100
    return dict(
        chosen,
        days=days,
        daily_rate_cents=rate,
        total_cents=rate * days,
        vehicle_ref=car["Reg"],
        vehicle_model=car["Model"],
        customer_name=customer["Name"],
    )


def request_id(payload):
    key = payload.get("request_id")
    if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", key):
        raise RentalError("Provide a valid request identifier.")
    return key


def replay(rows, payload):
    key = request_id(payload)
    row = next((r for r in rows if r["request_id"] == key), None)
    if row:
        fields = ["vehicle_id", "customer_id", "start_date", "end_date"]
        if any(row[k] != payload.get(k) for k in fields) or any(
            type(payload.get("quoted_" + k)) is not int
            or row[k] != payload.get("quoted_" + k)
            for k in ["total_cents", "daily_rate_cents"]
        ):
            raise RentalError(
                "That request identifier has already been used for a different selection.",
                "request_conflict",
                409,
            )
    return row


def confirm(cars, customers, rows, payload, asof):
    selection(payload)
    key = request_id(payload)
    existing = replay(rows, payload)
    if existing:
        return existing, False
    result = quote(cars, customers, rows, payload, asof)
    if any(
        type(payload.get("quoted_" + k)) is not int
        or payload["quoted_" + k] != result[k]
        for k in ["daily_rate_cents", "total_cents"]
    ):
        raise RentalError(
            "The daily rate or quotation changed. Review a fresh quote before confirming.",
            "quote_changed",
            409,
        )
    return (
        dict(
            result,
            id=max([r["id"] for r in rows], default=0) + 1,
            status="confirmed",
            request_id=key,
            created_on=asof,
        ),
        True,
    )


def transition(row, status, asof):
    if status not in ["cancelled", "completed"]:
        raise RentalError("Choose cancelled or completed.")
    if row["status"] == status:
        return dict(row)
    if row["status"] != "confirmed":
        raise RentalError(
            "A terminal reservation cannot be changed.", "invalid_transition", 409
        )
    if status == "completed" and row["end_date"] > asof:
        raise RentalError(
            "Complete this rental on or after its scheduled return date.",
            "return_not_due",
            409,
        )
    return dict(row, status=status, updated_on=asof)


def availability(cars, rows, start, end, asof):
    period(start, end, asof)
    return [
        dict(
            vehicle_id=c["id"],
            available=not any(
                r["vehicle_id"] == c["id"] and overlaps(r, start, end) for r in rows
            ),
        )
        for c in cars
    ]


def summary(cars, rows, start, end, asof):
    return dict(
        vehicles=len(cars),
        available=sum(
            r["available"] for r in availability(cars, rows, start, end, asof)
        ),
        active=sum(
            r["status"] == "confirmed" and r["start_date"] <= asof < r["end_date"]
            for r in rows
        ),
        upcoming=sum(
            r["status"] == "confirmed" and r["start_date"] > asof for r in rows
        ),
        return_due=sum(
            r["status"] == "confirmed" and r["end_date"] <= asof for r in rows
        ),
        confirmed_value_cents=sum(
            r["total_cents"] for r in rows if r["status"] == "confirmed"
        ),
    )


def seeded(cars, customers, spec, asof):
    rows = []
    anchor = calendar(asof)
    for i, s in enumerate(spec, 1):
        a = (anchor + timedelta(days=s["start_offset"])).isoformat()
        b = (anchor + timedelta(days=s["end_offset"])).isoformat()
        q = quote(
            cars,
            customers,
            rows,
            dict(
                vehicle_id=s["vehicle_id"],
                customer_id=s["customer_id"],
                start_date=a,
                end_date=b,
            ),
            a,
        )
        rows.append(
            dict(
                q,
                id=i,
                status="confirmed",
                request_id="seed-rental-" + str(i),
                created_on=a,
            )
        )
    return rows
