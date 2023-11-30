from CarDao import CarDao

car1 = {
    'id': 1,
    'reg': '11C10624',
    'model': 'Skoda Fabia',
    'price': 4500
}

car2 = {
    'id': 2,
    'reg': '10KY123',
    'model': 'Citroen Berlingo',
    'price': 3400
}


#returnValue = CarDao.create(car)
returnValue = CarDao.getAll()
print(returnValue)
