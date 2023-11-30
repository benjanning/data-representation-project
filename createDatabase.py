import pymysql

# Connect to MySQL
db = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="bencars"  
)

cursor = db.cursor()

# Create tables if not exists
cursor.execute("CREATE TABLE IF NOT EXISTS cars(\
    serialNum int NOT NULL AUTO_INCREMENT,\
    reg varchar(250),\
    model varchar(250),\
    price int,\
    PRIMARY KEY(serialNum)\
    )")

cursor.execute("CREATE TABLE IF NOT EXISTS customer(\
    serialNum int NOT NULL AUTO_INCREMENT,\
    reg varchar(250),\
    name varchar(250),\
    price int,\
    PRIMARY KEY(serialNum)\
    )")

# Insert data into tables
sql1 = "INSERT INTO cars (reg, model, price) VALUES ('11C10624', 'Skoda Fabia', 4500)"
sql2 = "INSERT INTO cars (reg, model, price) VALUES ('10KY123', 'Citroen Berlingo', 3400)"
sql3 = "INSERT INTO customer (reg, name, price) VALUES ('12D5678', 'Mercedes A Class', 32000)"
sql4 = "INSERT INTO customer (reg, name, price) VALUES ('11C10624', 'Skoda Fabia', 4500)"

cursor.execute(sql1)
cursor.execute(sql2)
cursor.execute(sql3)
cursor.execute(sql4)

# Commit changes and close the connection
db.commit()
db.close()
