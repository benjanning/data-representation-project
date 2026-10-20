from mysql_store import MySQLStore
class CustomerDAO(MySQLStore):
    def __init__(self):super().__init__('customer','Name')
CustomerDao=CustomerDAO()
