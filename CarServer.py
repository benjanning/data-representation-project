# Create a server for the virtual environment. 

from flask import Flask, jsonify, request, abort
from CarDao import CarDao

app = Flask(__name__)

@app.route('/')
def home(): #index page
    return app.send_static_file('CarServer.html')


#curl "http://127.0.0.1:5000/books"
@app.route('/cars')
def getAll():
    #print("in getall")
    results = CarDao.getAll()
    return jsonify(results)

#curl "http://127.0.0.1:5000/books/2"
@app.route('/cars/<int:id>')
def findById(id):
    foundCar = CarDao.findByID(id) 
    return jsonify(foundCar) 

#curl  -i -H "Content-Type:application/json" -X POST -d "{\"Title\":\"hello\",\"Author\":\"someone\",\"Price\":123}" http://127.0.0.1:5000/books
@app.route('/cars', methods=['POST'])
def create():
    
    if not request.json:
        abort(400)
    # other checking 
    car = {
        "Reg": request.json['Reg'],
        "Model": request.json['Model'],
        "Price": request.json['Price'],
    }
    values =(car['Reg'],car['Model'],car['Price'])
    newId = CarDao.create(values)
    car['id'] = newId
    return jsonify(car)

#curl  -i -H "Content-Type:application/json" -X PUT -d "{\"Title\":\"hello\",\"Author\":\"someone\",\"Price\":123}" http://127.0.0.1:5000/books/1
@app.route('/cars/<int:id>', methods=['PUT'])
def update(id):
    foundCar = CarDao.findByID(id)
    if not foundCar:
        abort(404)
    
    if not request.json:
        abort(400)
    reqJson = request.json
    if 'Price' in reqJson and type(reqJson['Price']) is not int:
        abort(400)

    if 'Reg' in reqJson:
        foundCar['Reg'] = reqJson['Reg']
    if 'Model' in reqJson:
        foundCar['Model'] = reqJson['Model']
    if 'Price' in reqJson:
        foundCar['Price'] = reqJson['Price']

    values = (foundCar['Reg'],foundCar['Model'],foundCar['Price'],foundCar['id'])

    CarDao.update(values)
    
    return jsonify(foundCar) 
        

    

@app.route('/cars/<int:id>' , methods=['DELETE'])
def delete(id):
    CarDao.delete(id)
    return jsonify({"done":True})




if __name__ == '__main__' :
    app.run(debug= True)