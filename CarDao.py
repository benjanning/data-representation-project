import mysql.connector
from mysql.connector import Error
import dbconfig as cfg

class CarDAO:
    def __init__(self):
        # Establish a connection to the MySQL database using credentials from the configuration file
        self.db = mysql.connector.connect(
            host=cfg.mysql['host'],
            user=cfg.mysql['user'],
            password=cfg.mysql['password'],
            database=cfg.mysql['database']
        )

    def create(self, car):
        # Create a new car entry in the database
        cursor = self.db.cursor()
        sql = "INSERT INTO cars (reg, model, price) VALUES (%s, %s, %s)"
        values = (car['Reg'], car['Model'], car['Price'])

        cursor.execute(sql, values)
        self.db.commit()  # Commit the transaction
        lastrowid = cursor.lastrowid  # Get the ID of the newly created record
        cursor.close()
        return lastrowid

    def getAll(self):
        # Retrieve all car entries from the database
        cursor = self.db.cursor()
        sql = "SELECT * FROM cars"
        cursor.execute(sql)
        results = cursor.fetchall()  # Fetch all rows of a query result
        cursor.close()
        return [self.convertToDictionary(result) for result in results]

    def findByID(self, id):
        # Find a car by its ID
        cursor = self.db.cursor()
        sql = "SELECT * FROM cars WHERE id = %s"
        values = (id,)

        cursor.execute(sql, values)
        result = cursor.fetchone()  # Fetch the first row of a query result
        cursor.close()
        return self.convertToDictionary(result) if result else None

    def update(self, id, car):
        # Update a car's details in the database
        cursor = self.db.cursor()
        sql = "UPDATE cars SET reg = %s, model = %s, price = %s WHERE id = %s"
        values = (car['Reg'], car['Model'], car['Price'], id)
        cursor.execute(sql, values)
        self.db.commit()  # Commit the transaction
        cursor.close()

    def delete(self, id):
        # Delete a car from the database
        cursor = self.db.cursor()
        sql = "DELETE FROM cars WHERE id = %s"
        values = (id,)

        cursor.execute(sql, values)
        self.db.commit()  # Commit the transaction
        cursor.close()

    def convertToDictionary(self, result):
        # Helper function to convert database row to a dictionary
        colnames = ['id', 'Reg', 'Model', 'Price']
        car = {colname: result[idx] for idx, colname in enumerate(colnames)}
        return car

# Instantiate the CarDAO to be used elsewhere
CarDao = CarDAO()
