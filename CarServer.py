from flask import Flask, jsonify, request, abort
from flask_httpauth import HTTPBasicAuth
import os
from werkzeug.exceptions import HTTPException

DEMO_MODE = os.getenv("DEMO_MODE") == "1"
if DEMO_MODE:
    from demo_store import CarDao, CustomerDAO
else:
    from CarDao import CarDao
    from CustomerDao import CustomerDAO

app = Flask(__name__, static_url_path='', static_folder='static')
auth = HTTPBasicAuth()

@app.before_request
def protect_api():
    # Demo records are synthetic and the development server binds to loopback.
    if not DEMO_MODE and request.path.startswith(('/cars', '/customer')):
        return auth.login_required(lambda: None)()

@app.errorhandler(400)
def bad_request(error):
    return jsonify(error='Invalid request'), 400


# Authentication details

# Explicit demo configuration is required. Never use hard-coded accounts
# in a publicly hosted app.
USER_DATA = {}
if os.getenv("DEMO_USERNAME") and os.getenv("DEMO_PASSWORD"):
    USER_DATA[os.environ["DEMO_USERNAME"]] = os.environ["DEMO_PASSWORD"]

@auth.verify_password
def verify_password(username, password):
    from hmac import compare_digest
    if username in USER_DATA and compare_digest(USER_DATA[username], password):
        return username

@app.route('/')
def home():
    if not DEMO_MODE:
        return auth.login_required(lambda: app.send_static_file('CarServer.html'))()
    # Serve the HTML file
    return app.send_static_file('CarServer.html')

# Initialize Customer Dao
CustomerDao = CustomerDAO()

def validate_record(record, label):
    if not isinstance(record, dict):
        abort(400)
    if not all(isinstance(record.get(k), str) and 0 < len(record[k].strip()) <= 250 for k in ['Reg', label]):
        abort(400)
    price = record.get('Price')
    try:
        if isinstance(price, bool):
            abort(400)
        numeric = float(price)
        import math
        if not math.isfinite(numeric) or not numeric.is_integer() or not 0 <= numeric <= 1000000000:
            abort(400)
    except (TypeError, ValueError):
        abort(400)
    record['Price'] = int(numeric)

# Cars Routes

@app.route('/cars', methods=['GET'])
def getAll():
    try:
        results = CarDao.getAll()
        return jsonify(results)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting cars: {e}")
        abort(500)

@app.route('/cars/<int:id>', methods=['GET'])
def findById(id):
    try:
        foundCar = CarDao.findByID(id)
        if foundCar:
            return jsonify(foundCar)
        else:
            abort(404)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error finding car with id {id}: {e}")
        abort(500)

@app.route('/cars', methods=['POST'])
def create():
    if not request.json:
        abort(400, 'Missing JSON in request')

    car_details = request.json
    validate_record(car_details, "Model")
    try:
        newId = CarDao.create(car_details)
        car_details['id'] = newId
        return jsonify(car_details), 201
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating car: {e}")
        abort(500)

@app.route('/cars/<int:id>', methods=['PUT'])
def update(id):
    foundCar = CarDao.findByID(id)
    if not foundCar:
        abort(404)

    if not request.json:
        abort(400, 'Missing JSON in request')

    try:
        validate_record(request.json, "Model")
        CarDao.update(id, request.json)
        return jsonify(request.json)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating car with id {id}: {e}")
        abort(500)

@app.route('/cars/<int:id>', methods=['DELETE'])
def delete(id):
    try:
        if not CarDao.findByID(id):
            abort(404)
        CarDao.delete(id)
        return jsonify({"done": True})
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting car with id {id}: {e}")
        abort(500)


# Customer Routes

@app.route('/customer', methods=['GET'])
def getAllCustomer():
    try:
        results = CustomerDao.getAll()
        return jsonify(results)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting customer: {e}")
        abort(500)

@app.route('/customer/<int:id>', methods=['GET'])
def findCustomerById(id):
    try:
        foundCustomer = CustomerDao.findByID(id)
        if foundCustomer:
            return jsonify(foundCustomer)
        else:
            abort(404)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error finding customer with id {id}: {e}")
        abort(500)

@app.route('/customer', methods=['POST'])
def createCustomer():
    if not request.json:
        abort(400, 'Missing JSON in request')

    customer_details = request.json
    validate_record(customer_details, "Name")
    try:
        newId = CustomerDao.create(customer_details)
        customer_details['id'] = newId
        return jsonify(customer_details), 201
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating customer: {e}")
        abort(500)

@app.route('/customer/<int:id>', methods=['PUT'])
def updateCustomer(id):
    foundCustomer = CustomerDao.findByID(id)
    if not foundCustomer:
        abort(404)

    if not request.json:
        abort(400, 'Missing JSON in request')

    try:
        validate_record(request.json, "Name")
        CustomerDao.update(id, request.json)
        return jsonify(request.json)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating customer with id {id}: {e}")
        abort(500)

@app.route('/customer/<int:id>', methods=['DELETE'])
def deleteCustomer(id):
    try:
        if not CustomerDao.findByID(id):
            abort(404)
        CustomerDao.delete(id)
        return jsonify({"done": True})
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting customer with id {id}: {e}")
        abort(500)

if __name__ == '__main__':
    app.run(host="127.0.0.1", debug=False)