"""Synthetic transactions share a lock with the existing CRUD resource mutations."""

from copy import deepcopy
from threading import RLock
from pathlib import Path
import json
import rentals


class RentalStore:
    def __init__(self, cars, customers):
        self.cars = cars
        self.customers = customers
        self.lock = RLock()
        self.reset()

    def reset(self):
        with self.lock:
            spec = json.loads(
                (Path(__file__).parent / "static/reservation-seed.json").read_text()
            )
            self.rows = rentals.seeded(
                self.cars.getAll(), self.customers.getAll(), spec, rentals.today()
            )

    def getAll(self):
        with self.lock:
            return deepcopy(self.rows)

    def quotation(self, payload, asof):
        with self.lock:
            return rentals.quote(
                self.cars.getAll(), self.customers.getAll(), self.rows, payload, asof
            )

    def create(self, payload, asof):
        with self.lock:
            row, created = rentals.confirm(
                self.cars.getAll(), self.customers.getAll(), self.rows, payload, asof
            )
            if created:
                self.rows.append(row)
            return deepcopy(row), created

    def change(self, id, status, asof):
        with self.lock:
            index = next((i for i, r in enumerate(self.rows) if r["id"] == id), None)
            if index is None:
                raise rentals.RentalError(
                    "Reservation no longer exists.", "reservation_missing", 404
                )
            self.rows[index] = rentals.transition(self.rows[index], status, asof)
            return deepcopy(self.rows[index])

    def guard_delete(self, kind, id):
        key = "vehicle_id" if kind == "cars" else "customer_id"
        if any(r[key] == id for r in self.rows):
            raise rentals.RentalError(
                "This record is referenced by reservation history and cannot be deleted.",
                "record_referenced",
                409,
            )
