# Create Database using Python 

import pymysql
from mysql.connector import cursor

# Connect to MySQL
db = pymysql.connect(
    host="localhost", 
    user = "root", 
    password = ""
    )


cursor = db.cursor() 
cursor.execute("DROP DATABASE IF EXISTS bencars")
cursor.execute("CREATE DATABASE bencars")
cursor.execute("USE bencars")


cursor.execute("CREATE TABLE cars(\
    id int NOT NULL AUTO_INCREMENT,\
    reg varchar(250),\
    model varchar(250),\
    price int,\
    PRIMARY KEY(id)\
    )") 

cursor.execute("CREATE TABLE customer(\
    id int NOT NULL AUTO_INCREMENT,\
    reg varchar(250),\
    name varchar(250),\
    price int,\
    PRIMARY KEY(id)\
    )") 

sql1= ("insert into cars (reg, model, price) values ('11C10623', 'Skoda Fabia', 13000)")

sql2= ("insert into cars (reg, model, price) values ('11K456', 'Audi A3', 20000)")

sql3= ("insert into customer (reg, name, price) values ('11C10623', 'John Smith', 13000)")

sql4= ("insert into customer (reg, name, price) values ('11K456', 'Thomas Hardy', 20000)")

cursor.execute(sql1)
cursor.execute(sql2)
cursor.execute(sql3)
cursor.execute(sql4)
db.commit()