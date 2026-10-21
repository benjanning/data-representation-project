import os, unittest, json

os.environ["DEMO_MODE"] = "1"
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch
import rentals
from CarServer import app, CarDao, Reservations


class RentalTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.post("/api/demo/reset", json={})
        self.asof = rentals.today()
        a = rentals.calendar(self.asof) + timedelta(days=10)
        self.choice = dict(
            vehicle_id=8,
            customer_id=4,
            start_date=a.isoformat(),
            end_date=(a + timedelta(days=3)).isoformat(),
        )

    def payload(self, key="request-test-001"):
        q = self.client.post("/api/reservations/quote", json=self.choice)
        self.assertEqual(q.status_code, 200, q.text)
        return dict(
            self.choice,
            request_id=key,
            quoted_daily_rate_cents=q.json["daily_rate_cents"],
            quoted_total_cents=q.json["total_cents"],
        )

    def test_quote_reconciles_calendar_and_rate(self):
        q = self.client.post("/api/reservations/quote", json=self.choice).json
        self.assertEqual(
            (q["days"], q["daily_rate_cents"], q["total_cents"]), (3, 6800, 20400)
        )
        for a, b, n in [
            ("2028-02-28", "2028-03-01", 2),
            ("2027-12-31", "2028-01-01", 1),
        ]:
            self.assertEqual(rentals.period(a, b, a), n)

    def test_invalid_shapes_dates_and_missing_references(self):
        for payload in [
            None,
            [],
            {},
            dict(self.choice, vehicle_id=True),
            dict(self.choice, start_date="2027-02-30"),
            dict(self.choice, end_date=self.choice["start_date"]),
        ]:
            self.assertEqual(
                self.client.post(
                    "/api/reservations/quote",
                    data=json.dumps(payload),
                    content_type="application/json",
                ).status_code,
                400,
            )
        self.assertEqual(
            self.client.post(
                "/api/reservations/quote", json=dict(self.choice, vehicle_id=99999)
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post("/api/reservations", json=self.choice).status_code, 400
        )

    def test_overlap_boundaries_cancellation_and_idempotency(self):
        p = self.payload()
        a = self.client.post("/api/reservations", json=p)
        self.assertEqual(a.status_code, 201)
        replay = self.client.post("/api/reservations", json=p)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(a.json, replay.json)
        self.assertEqual(
            self.client.post(
                "/api/reservations", json=dict(p, request_id="other-request-001")
            ).status_code,
            409,
        )
        for start, end in [
            (p["start_date"], p["end_date"]),
            (rentals.today(), p["end_date"]),
            (
                p["start_date"],
                (rentals.calendar(p["end_date"]) + timedelta(days=1)).isoformat(),
            ),
        ]:
            self.assertEqual(
                self.client.post(
                    "/api/reservations/quote",
                    json=dict(self.choice, start_date=start, end_date=end),
                ).status_code,
                409,
            )
        adjacent = dict(
            self.choice,
            start_date=p["end_date"],
            end_date=(rentals.calendar(p["end_date"]) + timedelta(days=2)).isoformat(),
        )
        self.assertEqual(
            self.client.post("/api/reservations/quote", json=adjacent).status_code, 200
        )
        self.assertEqual(
            self.client.post(
                "/api/reservations/" + str(a.json["id"]) + "/status",
                json={"status": "cancelled"},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post("/api/reservations/quote", json=self.choice).status_code,
            200,
        )
        self.assertEqual(
            self.client.post("/api/reservations", json=p).json["status"], "cancelled"
        )

    def test_stale_quotes_and_snapshots(self):
        p = self.payload()
        car = self.client.get("/cars/8").json
        self.client.put("/cars/8", json=dict(car, Price=70))
        self.assertEqual(
            self.client.post("/api/reservations", json=p).json["code"], "quote_changed"
        )
        created = self.client.post("/api/reservations", json=self.payload()).json
        self.client.put(
            "/cars/8", json=dict(car, Price=99, Model="Changed description")
        )
        stored = next(
            r
            for r in self.client.get("/api/reservations").json
            if r["id"] == created["id"]
        )
        self.assertEqual(stored["vehicle_model"], car["Model"])
        self.assertEqual(stored["daily_rate_cents"], 7000)

    def test_tampered_totals_replay_conflicts_and_referenced_deletion(self):
        p = self.payload()
        self.assertEqual(
            self.client.post(
                "/api/reservations", json=dict(p, quoted_total_cents=1)
            ).status_code,
            409,
        )
        self.client.post("/api/reservations", json=p)
        self.assertEqual(
            self.client.post("/api/reservations", json=dict(p, customer_id=5)).json[
                "code"
            ],
            "request_conflict",
        )
        for route in ["/cars/8", "/customer/4"]:
            self.assertEqual(
                self.client.delete(route).json["code"], "record_referenced"
            )

    def test_state_transitions_and_summary(self):
        rows = self.client.get("/api/reservations").json
        active = rows[0]
        due = rows[2]
        self.assertEqual(
            self.client.post(
                f"/api/reservations/{active['id']}/status", json={"status": "completed"}
            ).status_code,
            409,
        )
        done = self.client.post(
            f"/api/reservations/{due['id']}/status", json={"status": "completed"}
        )
        self.assertEqual(done.status_code, 200)
        self.assertEqual(
            self.client.post(
                f"/api/reservations/{due['id']}/status", json={"status": "cancelled"}
            ).status_code,
            409,
        )
        metrics = rentals.summary(
            CarDao.getAll(),
            Reservations.getAll(),
            self.asof,
            (rentals.calendar(self.asof) + timedelta(days=1)).isoformat(),
            self.asof,
        )
        self.assertEqual(
            (
                metrics["vehicles"],
                metrics["available"],
                metrics["active"],
                metrics["upcoming"],
                metrics["return_due"],
            ),
            (8, 7, 1, 1, 0),
        )
        self.assertEqual(metrics["confirmed_value_cents"], 4 * 3900 + 3 * 4900)

    def test_concurrent_overlap_has_one_winner(self):
        p = self.payload()

        def create(n):
            with app.test_client() as client:
                return client.post(
                    "/api/reservations", json=dict(p, request_id="concurrent-" + str(n))
                ).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(create, [1, 2]))
        self.assertEqual(sorted(results), [201, 409])
        self.assertEqual(len(Reservations.getAll()), 4)

    def test_safe_storage_failure_reset_and_cross_origin(self):
        with patch.object(
            Reservations,
            "quotation",
            side_effect=RuntimeError("secret database message"),
        ):
            response = self.client.post("/api/reservations/quote", json=self.choice)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret database message", response.text)
        self.assertEqual(
            self.client.post(
                "/api/reservations",
                json=self.payload(),
                headers={"Origin": "https://unrelated.example"},
            ).status_code,
            403,
        )
        self.client.post("/api/reservations", json=self.payload())
        self.client.post("/api/demo/reset", json={})
        self.assertEqual(len(self.client.get("/api/reservations").json), 3)


if __name__ == "__main__":
    unittest.main()
