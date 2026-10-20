from mysql_store import MySQLStore
class CarDAO(MySQLStore):
    def __init__(self):super().__init__('cars','Model')
CarDao=CarDAO()
