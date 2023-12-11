import mysql.connector
from mysql.connector import Error
import dbconfig as cfg

class CustomerDAO:
    def __init__(self):
        # Establish a connection to the MySQL database using credentials from the configuration file
        self.db = mysql.connector.connect(
            host=cfg.mysql['host'],
            user=cfg.mysql['user'],
            password=cfg.mysql['password'],
            database=cfg.mysql['database']
        )

    def create(self, customer):
        # Create a new customer entry in the database
        cursor = self.db.cursor()
        sql = "INSERT INTO customer (reg, name, price) VALUES (%s, %s, %s)"
        values = (customer['Reg'], customer['Name'], customer['Price'])

        cursor.execute(sql, values)
        self.db.commit()  # Commit the transaction
        lastrowid = cursor.lastrowid  # Get the ID of the newly created record
        cursor.close()
        return lastrowid

    def getAll(self):
        # Retrieve all customer entries from the database
        cursor = self.db.cursor()
        sql = "SELECT * FROM customer"
        cursor.execute(sql)
        results = cursor.fetchall()  # Fetch all rows of a query result
        cursor.close()
        return [self.convertToDictionary(result) for result in results]

    def findByID(self, id):
        # Find a customer by their ID
        cursor = self.db.cursor()
        sql = "SELECT * FROM customer WHERE id = %s"
        values = (id,)

        cursor.execute(sql, values)
        result = cursor.fetchone()  # Fetch the first row of a query result
        cursor.close()
        return self.convertToDictionary(result) if result else None

    def update(self, id, customer):
        # Update a customer's details in the database
        cursor = self.db.cursor()
        sql = "UPDATE customer SET reg = %s, name = %s, price = %s WHERE id = %s"
        values = (customer['Reg'], customer['Name'], customer['Price'], id)
        cursor.execute(sql, values)
        self.db.commit()  # Commit the transaction
        cursor.close()

    def delete(self, id):
        # Delete a customer from the database
        cursor = self.db.cursor()
        sql = "DELETE FROM customer WHERE id = %s"
        values = (id,)

        cursor.execute(sql, values)
        self.db.commit()  # Commit the transaction
        cursor.close()

    def convertToDictionary(self, result):
        # Helper function to convert database row to a dictionary
        colnames = ['id', 'Reg', 'Name', 'Price']
        customer = {colname: result[idx] for idx, colname in enumerate(colnames)}
        return customer

# Instantiate the CustomerDAO to be used elsewhere
CustomerDao = CustomerDAO()
