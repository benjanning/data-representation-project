from flask import Flask, jsonify, request, abort
from CarDao import CarDao

app = Flask(__name__, static_url_path='', static_folder='static')

@app.route('/')
def home():
    # Serve the HTML file
    return app.send_static_file('carserver.html')

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

if __name__ == '__main__':
    app.run(debug=True)
