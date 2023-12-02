import mysql.connector
from mysql.connector import Error
import dbconfig as cfg

class CarDAO:
    def __init__(self):
        self.db = mysql.connector.connect(
            host=cfg.mysql['host'],
            user=cfg.mysql['user'],
            password=cfg.mysql['password'],
            database=cfg.mysql['database']
        )

    def create(self, car):
        cursor = self.db.cursor()
        sql = "INSERT INTO cars (reg, model, price) VALUES (%s, %s, %s)"
        values = (car['Reg'], car['Model'], car['Price'])

        cursor.execute(sql, values)
        self.db.commit()
        lastrowid = cursor.lastrowid
        cursor.close()
        return lastrowid

    def getAll(self):
        cursor = self.db.cursor()
        sql = "SELECT * FROM cars"
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        return [self.convertToDictionary(result) for result in results]

    def findByID(self, id):
        cursor = self.db.cursor()
        sql = "SELECT * FROM cars WHERE id = %s"
        values = (id,)

        cursor.execute(sql, values)
        result = cursor.fetchone()
        cursor.close()
        return self.convertToDictionary(result) if result else None

    def update(self, id, car):
        cursor = self.db.cursor()
        sql = "UPDATE cars SET reg = %s, model = %s, price = %s WHERE id = %s"
        values = (car['Reg'], car['Model'], car['Price'], id)
        cursor.execute(sql, values)
        self.db.commit()
        cursor.close()

    def delete(self, id):
        cursor = self.db.cursor()
        sql = "DELETE FROM cars WHERE id = %s"
        values = (id,)

        cursor.execute(sql, values)
        self.db.commit()
        cursor.close()

    def convertToDictionary(self, result):
        colnames = ['id', 'Reg', 'Model', 'Price']
        car = {colname: result[idx] for idx, colname in enumerate(colnames)}
        return car

CarDao = CarDAO()
