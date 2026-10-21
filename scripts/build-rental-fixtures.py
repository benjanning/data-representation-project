"""Generate deterministic Python reference cases for the JavaScript rules contract."""

from pathlib import Path
import sys, json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import rentals

seed = json.loads((ROOT / "static/demo-data.json").read_text())
cars = seed["cars"]
customers = seed["customers"]
now = "2030-01-01"
choice = dict(
    vehicle_id=8, customer_id=4, start_date="2030-01-10", end_date="2030-01-13"
)
payload = dict(
    choice,
    request_id="contract-request-1",
    quoted_daily_rate_cents=6800,
    quoted_total_cents=20400,
)
row, _ = rentals.confirm(cars, customers, [], payload, now)
cases = []


def case(name, method, args):
    try:
        value = getattr(rentals, method)(*args)
        expected = {"value": value}
    except rentals.RentalError as e:
        expected = {"error": dict(message=str(e), code=e.code, status=e.status)}
    cases.append(dict(name=name, method=method, args=args, expected=expected))


for name, a, b in [
    ("valid", "2030-01-10", "2030-01-13"),
    ("past", "2029-12-31", "2030-01-02"),
    ("same", "2030-01-10", "2030-01-10"),
    ("reversed", "2030-01-11", "2030-01-10"),
    ("impossible", "2030-02-30", "2030-03-04"),
    ("too-long", "2030-01-01", "2031-01-02"),
    ("too-far", "2031-01-02", "2031-01-03"),
    ("year-zero", "0000-01-01", "0000-01-02"),
]:
    case(
        name,
        "quote",
        [cars, customers, [], dict(choice, start_date=a, end_date=b), now],
    )
for name, changes in [
    ("missing", {"vehicle_id": 9999}),
    ("bool-id", {"vehicle_id": True}),
    ("huge-id", {"vehicle_id": 2**40}),
]:
    case(name, "quote", [cars, customers, [], dict(choice, **changes), now])
for name, a, b in [
    ("equal", "2030-01-10", "2030-01-13"),
    ("inside", "2030-01-11", "2030-01-12"),
    ("surround", "2030-01-09", "2030-01-14"),
    ("left", "2030-01-09", "2030-01-11"),
    ("right", "2030-01-12", "2030-01-14"),
    ("adjacent-before", "2030-01-08", "2030-01-10"),
    ("adjacent-after", "2030-01-13", "2030-01-15"),
]:
    case(
        name,
        "quote",
        [cars, customers, [row], dict(choice, start_date=a, end_date=b), now],
    )
case("create", "confirm", [cars, customers, [], payload, now])
case("retry", "confirm", [cars, customers, [row], payload, now])
case(
    "tampered",
    "confirm",
    [cars, customers, [], dict(payload, quoted_total_cents=1), now],
)
case(
    "reused-key", "confirm", [cars, customers, [row], dict(payload, customer_id=3), now]
)
for status, asof in [
    ("completed", now),
    ("completed", "2030-01-13"),
    ("cancelled", now),
    ("confirmed", now),
]:
    case(status + asof, "transition", [row, status, asof])
case("summary", "summary", [cars, [row], "2030-01-10", "2030-01-13", now])
path = ROOT / "tests/rental-contract.json"
text = json.dumps(cases, indent=2, ensure_ascii=False) + "\n"
if "--check" in sys.argv:
    if path.read_text(encoding="utf-8") != text:
        raise SystemExit("Rental contract fixture changed; regenerate and review it.")
else:
    path.write_text(text, encoding="utf-8")
print(len(cases), "Python rental contract cases verified")
