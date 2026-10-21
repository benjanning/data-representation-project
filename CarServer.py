from flask import Flask, jsonify, request, abort, Response
from flask_httpauth import HTTPBasicAuth
from werkzeug.exceptions import HTTPException
from pathlib import Path
from urllib.parse import urlparse
from validation import validate_record
import os
from functools import wraps
import rentals

DEMO_MODE = os.getenv("DEMO_MODE") == "1"
if DEMO_MODE:
    from demo_store import CarDao, CustomerDAO, SEED
else:
    from CarDao import CarDao
    from CustomerDao import CustomerDAO
app = Flask(__name__, static_url_path="", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 16384
auth = HTTPBasicAuth()
CustomerDao = CustomerDAO()
if DEMO_MODE:
    from rental_store import RentalStore

    Reservations = RentalStore(CarDao, CustomerDao)
else:
    from rental_mysql import RentalMySQL

    Reservations = RentalMySQL()
USER_DATA = {}
if os.getenv("DEMO_USERNAME") and os.getenv("DEMO_PASSWORD"):
    USER_DATA[os.environ["DEMO_USERNAME"]] = os.environ["DEMO_PASSWORD"]


@auth.verify_password
def verify_password(username, password):
    from hmac import compare_digest

    if username in USER_DATA and compare_digest(USER_DATA[username], password):
        return username


@app.before_request
def protect_api():
    if request.method in ["POST", "PUT", "DELETE"]:
        origin = request.headers.get("Origin")
        if origin and urlparse(origin).netloc != request.host:
            abort(403, "Cross-origin changes are not allowed.")
    if not DEMO_MODE and (
        request.path == "/" or request.path.startswith(("/cars", "/customer", "/api/"))
    ):
        return auth.login_required(lambda: None)()


@app.after_request
def headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
    )
    if request.path.startswith(("/cars", "/customer", "/api/")):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(HTTPException)
def known_error(e):
    descriptions = {
        400: "Invalid request.",
        404: "This record no longer exists. Refresh and try again.",
        405: "This action is not supported.",
        413: "The submitted record is too large.",
        415: "Send a JSON object.",
    }
    return jsonify(error=descriptions.get(e.code, e.description)), e.code


@app.errorhandler(Exception)
def unavailable(e):
    if getattr(e, "errno", None) == 1451:
        return (
            jsonify(
                error="This record is referenced by reservation history and cannot be deleted.",
                code="record_referenced",
            ),
            409,
        )
    app.logger.error("Record storage request failed: %s", type(e).__name__)
    return (
        jsonify(
            error="Record storage is unavailable. Your form is preserved; try again."
        ),
        503,
    )


@app.errorhandler(rentals.RentalError)
def rental_error(e):
    return jsonify(error=str(e), code=e.code), e.status


def serialise(action):
    @wraps(action)
    def wrapped(*args, **kwargs):
        if DEMO_MODE:
            with Reservations.lock:
                return action(*args, **kwargs)
        return action(*args, **kwargs)

    return wrapped


@app.route("/")
@app.route("/CarServer.html")
def home():
    html = (Path(app.static_folder) / "index.html").read_text(encoding="utf-8")
    return Response(
        html.replace('data-mode="static"', 'data-mode="server"'), mimetype="text/html"
    )


def register(route, store, label):
    def listing():
        return jsonify(store.getAll())

    def find(id):
        record = store.findByID(id)
        if not record:
            abort(404)
        return jsonify(record)

    def write(id=None):
        if id is not None and not store.findByID(id):
            abort(404)
        try:
            record = validate_record(request.get_json(), label)
        except ValueError as e:
            return jsonify(error=str(e)), 400
        duplicate = next(
            (
                v
                for v in store.getAll()
                if v["id"] != id
                and v["Reg"].casefold() == record["Reg"].casefold()
                and (
                    label == "Model"
                    or v["Name"].casefold() == record["Name"].casefold()
                )
            ),
            None,
        )
        if duplicate:
            return (
                jsonify(
                    error="That vehicle reference or customer/reference pair already exists."
                ),
                409,
            )
        if id is None:
            id = store.create(record)
            status = 201
        else:
            store.update(id, record)
            status = 200
        return jsonify(dict(record, id=id)), status

    def delete(id):
        if not store.findByID(id):
            abort(404)
        if DEMO_MODE:
            Reservations.guard_delete("cars" if label == "Model" else "customers", id)
        store.delete(id)
        return jsonify(done=True)

    app.add_url_rule(route, route + "list", serialise(listing), methods=["GET"])
    app.add_url_rule(route, route + "create", serialise(write), methods=["POST"])
    app.add_url_rule(
        route + "/<int:id>", route + "find", serialise(find), methods=["GET"]
    )
    app.add_url_rule(
        route + "/<int:id>", route + "update", serialise(write), methods=["PUT"]
    )
    app.add_url_rule(
        route + "/<int:id>", route + "delete", serialise(delete), methods=["DELETE"]
    )


register("/cars", CarDao, "Model")
register("/customer", CustomerDao, "Name")


@app.post("/api/demo/reset")
@serialise
def reset():
    if not DEMO_MODE:
        abort(404)
    CarDao.reset(SEED["cars"])
    CustomerDao.reset(SEED["customers"])
    Reservations.reset()
    return jsonify(done=True)


@app.get("/api/mode")
def mode():
    return jsonify(mode="synthetic Flask" if DEMO_MODE else "MySQL", reset=DEMO_MODE)


@app.get("/api/reservations")
def reservation_list():
    return jsonify(Reservations.getAll())


@app.post("/api/reservations/quote")
def reservation_quote():
    return jsonify(Reservations.quotation(request.get_json(), rentals.today()))


@app.post("/api/reservations")
def reservation_create():
    row, created = Reservations.create(request.get_json(), rentals.today())
    return jsonify(row), 201 if created else 200


@app.post("/api/reservations/<int:id>/status")
def reservation_change(id):
    payload = request.get_json()
    if not isinstance(payload, dict):
        raise rentals.RentalError("Provide a status object.")
    return jsonify(Reservations.change(id, payload.get("status"), rentals.today()))


@app.get("/api/availability")
@serialise
def reservation_availability():
    return jsonify(
        rentals.availability(
            CarDao.getAll(),
            Reservations.getAll(),
            request.args.get("start_date"),
            request.args.get("end_date"),
            rentals.today(),
        )
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 5000)), debug=False)
