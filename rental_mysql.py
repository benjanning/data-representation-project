"""Transactional rental allocation, serialized by locking the vehicle row."""

from contextlib import contextmanager
from threading import RLock
from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector import IntegrityError
import dbconfig as cfg
import rentals

SCHEMA = """CREATE TABLE IF NOT EXISTS fleet_reservations (
 id INT AUTO_INCREMENT PRIMARY KEY,
 vehicle_id INT NOT NULL, customer_id INT NOT NULL,
 start_date DATE NOT NULL, end_date DATE NOT NULL, days INT NOT NULL,
 daily_rate_cents BIGINT NOT NULL, total_cents BIGINT NOT NULL,
 vehicle_ref VARCHAR(250) NOT NULL, vehicle_model VARCHAR(250) NOT NULL,
 customer_name VARCHAR(250) NOT NULL,
 status VARCHAR(12) NOT NULL, request_id VARCHAR(80) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
 created_on DATE NOT NULL, updated_on DATE NULL,
 INDEX vehicle_period(vehicle_id,status,start_date,end_date),
 FOREIGN KEY(vehicle_id) REFERENCES cars(id),
 FOREIGN KEY(customer_id) REFERENCES customer(id),
 CHECK(end_date>start_date), CHECK(status IN ('confirmed','cancelled','completed'))
) ENGINE=InnoDB"""


def migrate(connection):
    cursor = connection.cursor()
    try:
        cursor.execute(SCHEMA)
        connection.commit()
    finally:
        cursor.close()


def convert(row):
    if not row:
        return None
    return {
        k: (v.isoformat() if hasattr(v, "isoformat") else v)
        for k, v in row.items()
        if v is not None
    }


class RentalMySQL:
    def __init__(self):
        self.pool = None
        self.pool_lock = RLock()

    @contextmanager
    def transaction(self):
        with self.pool_lock:
            if self.pool is None:
                self.pool = MySQLConnectionPool(
                    pool_name="portfolio_rentals",
                    pool_size=4,
                    connection_timeout=5,
                    **cfg.mysql
                )
        db = self.pool.get_connection()
        cursor = None
        try:
            db.start_transaction(isolation_level="READ COMMITTED")
            cursor = db.cursor(dictionary=True)
            yield cursor
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            db.close()

    def getAll(self):
        with self.transaction() as c:
            c.execute("SELECT * FROM fleet_reservations ORDER BY id")
            return [convert(r) for r in c.fetchall()]

    @staticmethod
    def inputs(c, payload, lock=False):
        chosen = rentals.selection(payload)
        suffix = " FOR UPDATE" if lock else ""
        c.execute(
            "SELECT id,reg AS Reg,model AS Model,price AS Price FROM cars WHERE id=%s"
            + suffix,
            (chosen["vehicle_id"],),
        )
        car = c.fetchone()
        c.execute(
            "SELECT id,name AS Name FROM customer WHERE id=%s" + suffix,
            (chosen["customer_id"],),
        )
        customer = c.fetchone()
        c.execute(
            "SELECT * FROM fleet_reservations WHERE vehicle_id=%s",
            (chosen["vehicle_id"],),
        )
        rows = [convert(r) for r in c.fetchall()]
        return [car] if car else [], [customer] if customer else [], rows

    def quotation(self, payload, asof):
        with self.transaction() as c:
            return rentals.quote(*self.inputs(c, payload), payload, asof)

    def create(self, payload, asof):
        rentals.selection(payload)
        key = rentals.request_id(payload)
        try:
            with self.transaction() as c:
                cars, customers, rows = self.inputs(c, payload, True)
                c.execute(
                    "SELECT * FROM fleet_reservations WHERE request_id=%s", (key,)
                )
                existing = c.fetchone()
                if existing:
                    return rentals.replay([convert(existing)], payload), False
                row, created = rentals.confirm(cars, customers, rows, payload, asof)
                fields = [k for k in row if k != "id"]
                c.execute(
                    "INSERT INTO fleet_reservations ("
                    + ",".join(fields)
                    + ") VALUES ("
                    + ",".join(["%s"] * len(fields))
                    + ")",
                    tuple(row[k] for k in fields),
                )
                row["id"] = c.lastrowid
                return row, created
        except IntegrityError as error:
            if error.errno != 1062:
                raise
            with self.transaction() as c:
                c.execute(
                    "SELECT * FROM fleet_reservations WHERE request_id=%s", (key,)
                )
                existing = c.fetchone()
                if not existing:
                    raise
                return rentals.replay([convert(existing)], payload), False

    def change(self, id, status, asof):
        with self.transaction() as c:
            c.execute("SELECT vehicle_id FROM fleet_reservations WHERE id=%s", (id,))
            found = c.fetchone()
            if not found:
                raise rentals.RentalError(
                    "Reservation no longer exists.", "reservation_missing", 404
                )
            c.execute(
                "SELECT id FROM cars WHERE id=%s FOR UPDATE", (found["vehicle_id"],)
            )
            c.fetchone()
            c.execute("SELECT * FROM fleet_reservations WHERE id=%s FOR UPDATE", (id,))
            row = rentals.transition(convert(c.fetchone()), status, asof)
            c.execute(
                "UPDATE fleet_reservations SET status=%s,updated_on=%s WHERE id=%s",
                (row["status"], row.get("updated_on"), id),
            )
            return row
