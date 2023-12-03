import mysql.connector
from mysql.connector import Error
import dbconfig as cfg

class CustomerDAO:
    def __init__(self):
        self.db = mysql.connector.connect(
            host=cfg.mysql['host'],
            user=cfg.mysql['user'],
            password=cfg.mysql['password'],
            database=cfg.mysql['database']
        )

    def create(self, customer):
        cursor = self.db.cursor()
        sql = "INSERT INTO customer (reg, name, price) VALUES (%s, %s, %s)"
        values = (customer['Reg'], customer['Name'], customer['Price'])

        cursor.execute(sql, values)
        self.db.commit()
        lastrowid = cursor.lastrowid
        cursor.close()
        return lastrowid

    def getAll(self):
        cursor = self.db.cursor()
        sql = "SELECT * FROM customer"
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        return [self.convertToDictionary(result) for result in results]

    def findByID(self, id):
        cursor = self.db.cursor()
        sql = "SELECT * FROM customer WHERE id = %s"
        values = (id,)

        cursor.execute(sql, values)
        result = cursor.fetchone()
        cursor.close()
        return self.convertToDictionary(result) if result else None

    def update(self, id, customer):
        cursor = self.db.cursor()
        sql = "UPDATE customer SET reg = %s, name = %s, price = %s WHERE id = %s"
        values = (customer['Reg'], customer['Name'], customer['Price'], id)
        cursor.execute(sql, values)
        self.db.commit()
        cursor.close()

    def delete(self, id):
        cursor = self.db.cursor()
        sql = "DELETE FROM customers WHERE id = %s"
        values = (id,)

        cursor.execute(sql, values)
        self.db.commit()
        cursor.close()

    def convertToDictionary(self, result):
        colnames = ['id', 'Reg', 'Name', 'Price']
        customer = {colname: result[idx] for idx, colname in enumerate(colnames)}
        return customer

CustomerDao = CustomerDAO()
