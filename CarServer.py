from flask import Flask, jsonify, request, abort
from flask_httpauth import HTTPBasicAuth
from CarDao import CarDao
from CustomerDao import CustomerDAO

app = Flask(__name__, static_url_path='', static_folder='static')
auth = HTTPBasicAuth()

# Authentication details
USER_DATA = {
    "user": "password"
}

@auth.verify_password
def verify_password(username, password):
    if username in USER_DATA and USER_DATA[username] == password:
        return username

@app.route('/')
@auth.login_required
def home():
    # Serve the HTML file
    return app.send_static_file('carserver.html')

# Initialize Customer Dao
CustomerDao = CustomerDAO()

# Cars Routes

@app.route('/cars', methods=['GET'])
def getAll():
    try:
        results = CarDao.getAll()
        return jsonify(results)
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
    except Exception as e:
        print(f"Error finding car with id {id}: {e}")
        abort(500)

@app.route('/cars', methods=['POST'])
def create():
    if not request.json:
        abort(400, 'Missing JSON in request')

    car_details = request.json
    try:
        newId = CarDao.create(car_details)
        car_details['id'] = newId
        return jsonify(car_details), 201
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
        CarDao.update(id, request.json)
        return jsonify(request.json)
    except Exception as e:
        print(f"Error updating car with id {id}: {e}")
        abort(500)

@app.route('/cars/<int:id>', methods=['DELETE'])
def delete(id):
    try:
        CarDao.delete(id)
        return jsonify({"done": True})
    except Exception as e:
        print(f"Error deleting car with id {id}: {e}")
        abort(500)


# Customer Routes


@app.route('/customer', methods=['GET'])
def getAllCustomer():
    try:
        results = CustomerDao.getAll()
        return jsonify(results)
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
    except Exception as e:
        print(f"Error finding customer with id {id}: {e}")
        abort(500)

@app.route('/customer', methods=['POST'])
def createCustomer():
    if not request.json:
        abort(400, 'Missing JSON in request')

    customer_details = request.json
    try:
        newId = CustomerDao.create(customer_details)
        customer_details['id'] = newId
        return jsonify(customer_details), 201
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
        CustomerDao.update(id, request.json)
        return jsonify(request.json)
    except Exception as e:
        print(f"Error updating customer with id {id}: {e}")
        abort(500)

@app.route('/customer/<int:id>', methods=['DELETE'])
def deleteCustomer(id):
    try:
        CustomerDao.delete(id)
        return jsonify({"done": True})
    except Exception as e:
        print(f"Error deleting customer with id {id}: {e}")
        abort(500)

if __name__ == '__main__':
    app.run(debug=True)