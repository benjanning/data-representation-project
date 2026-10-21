"""Transactional allocation in the explicitly disposable CI database only."""

import os, unittest, base64, importlib.util
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch
import rentals


@unittest.skipUnless(
    os.getenv("RUN_MYSQL_TESTS") == "1", "Disposable MySQL integration is opt-in"
)
class RentalIntegration(unittest.TestCase):
    def test_transactional_overlap_snapshots_retry_and_foreign_keys(self):
        import mysql.connector
        from rental_mysql import migrate

        config = dict(
            host=os.environ["DB_HOST"],
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
        )
        if config["database"] != "portfolio_integration":
            raise RuntimeError(
                "Only the disposable portfolio_integration database is allowed."
            )
        db = mysql.connector.connect(**config)
        c = db.cursor()
        try:
            for table, column in [("cars", "model"), ("customer", "name")]:
                c.execute(
                    f"CREATE TABLE IF NOT EXISTS {table}(id INT AUTO_INCREMENT PRIMARY KEY,reg VARCHAR(250),{column} VARCHAR(250),price INT)"
                )
            db.commit()
            migrate(db)
            migrate(db)
        finally:
            c.close()
            db.close()
        with patch.dict(os.environ, DEMO_MODE="0"):
            spec = importlib.util.spec_from_file_location(
                "rental_mysql_app", Path(__file__).with_name("CarServer.py")
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        client = module.app.test_client()
        self.assertEqual(client.get("/api/reservations").status_code, 401)
        auth = base64.b64encode(
            (os.environ["DEMO_USERNAME"] + ":" + os.environ["DEMO_PASSWORD"]).encode()
        ).decode()
        headers = {"Authorization": "Basic " + auth}
        car = client.post(
            "/cars",
            headers=headers,
            json=dict(Reg="RENTAL-CI", Model="Synthetic rental integration", Price=43),
        )
        customer = client.post(
            "/customer",
            headers=headers,
            json=dict(Reg="RENTAL-CI", Name="Integration Sample", Price=43),
        )
        self.assertEqual(car.status_code, 201)
        self.assertEqual(customer.status_code, 201)
        vehicle_id = car.json["id"]
        customer_id = customer.json["id"]
        try:
            a = rentals.calendar(rentals.today()) + timedelta(days=15)
            b = a + timedelta(days=3)
            choice = dict(
                vehicle_id=vehicle_id,
                customer_id=customer_id,
                start_date=a.isoformat(),
                end_date=b.isoformat(),
            )
            q = client.post("/api/reservations/quote", headers=headers, json=choice)
            self.assertEqual(q.status_code, 200, q.text)
            self.assertEqual(q.json["total_cents"], 12900)
            payload = dict(
                choice, quoted_total_cents=12900, quoted_daily_rate_cents=4300
            )

            def create(n):
                with module.app.test_client() as worker:
                    return worker.post(
                        "/api/reservations",
                        headers=headers,
                        json=dict(payload, request_id="integration-race-" + str(n)),
                    )

            with ThreadPoolExecutor(max_workers=2) as pool:
                responses = list(pool.map(create, [1, 2]))
            self.assertEqual(
                sorted(r.status_code for r in responses),
                [201, 409],
                [r.text for r in responses],
            )
            winner = next(r.json for r in responses if r.status_code == 201)
            retry = client.post(
                "/api/reservations",
                headers=headers,
                json=dict(payload, request_id=winner["request_id"]),
            )
            self.assertEqual(retry.status_code, 200)
            self.assertEqual(retry.json, winner)
            for route in [f"/cars/{vehicle_id}", f"/customer/{customer_id}"]:
                self.assertEqual(client.delete(route, headers=headers).status_code, 409)
            car_payload = dict(Reg="RENTAL-CI", Model="Updated description", Price=47)
            self.assertEqual(
                client.put(
                    f"/cars/{vehicle_id}", headers=headers, json=car_payload
                ).status_code,
                200,
            )
            rows = client.get("/api/reservations", headers=headers).json
            stored = next(r for r in rows if r["id"] == winner["id"])
            self.assertEqual(stored["daily_rate_cents"], 4300)
            self.assertEqual(stored["vehicle_model"], "Synthetic rental integration")
            adjacent = dict(
                choice,
                start_date=b.isoformat(),
                end_date=(b + timedelta(days=2)).isoformat(),
            )
            stale = dict(
                adjacent,
                request_id="integration-stale",
                quoted_daily_rate_cents=4300,
                quoted_total_cents=8600,
            )
            self.assertEqual(
                client.post("/api/reservations", headers=headers, json=stale).json[
                    "code"
                ],
                "quote_changed",
            )
            self.assertEqual(
                client.post(
                    f"/api/reservations/{winner['id']}/status",
                    headers=headers,
                    json={"status": "completed"},
                ).status_code,
                409,
            )
            self.assertEqual(
                client.post(
                    f"/api/reservations/{winner['id']}/status",
                    headers=headers,
                    json={"status": "cancelled"},
                ).status_code,
                200,
            )
            self.assertEqual(
                client.post(
                    "/api/reservations/quote", headers=headers, json=choice
                ).status_code,
                200,
            )
            next_quote = client.post(
                "/api/reservations/quote", headers=headers, json=adjacent
            ).json
            following = client.post(
                "/api/reservations",
                headers=headers,
                json=dict(
                    adjacent,
                    request_id="integration-following",
                    quoted_daily_rate_cents=next_quote["daily_rate_cents"],
                    quoted_total_cents=next_quote["total_cents"],
                ),
            )
            self.assertEqual(following.status_code, 201, following.text)
            with patch.object(
                rentals, "today", return_value=following.json["end_date"]
            ):
                self.assertEqual(
                    client.post(
                        f"/api/reservations/{following.json['id']}/status",
                        headers=headers,
                        json={"status": "completed"},
                    ).status_code,
                    200,
                )
        finally:
            db = mysql.connector.connect(**config)
            c = db.cursor()
            try:
                c.execute(
                    "DELETE FROM fleet_reservations WHERE vehicle_id=%s", (vehicle_id,)
                )
                db.commit()
            finally:
                c.close()
                db.close()
            self.assertEqual(
                client.delete(f"/cars/{vehicle_id}", headers=headers).status_code, 200
            )
            self.assertEqual(
                client.delete(f"/customer/{customer_id}", headers=headers).status_code,
                200,
            )


if __name__ == "__main__":
    unittest.main()
