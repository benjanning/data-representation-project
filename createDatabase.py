# Create Database using Python 

import pymysql
from mysql.connector import cursor

# Use explicit configuration; never drop an existing database.
import dbconfig as cfg
import re
name = cfg.mysql['database']
if not re.fullmatch(r'[A-Za-z0-9_]+', name):
    raise ValueError('DB_NAME must contain only letters, digits and underscores')
db = pymysql.connect(host=cfg.mysql['host'], user=cfg.mysql['user'], password=cfg.mysql['password'])
cursor = db.cursor()
cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{name}`")
cursor.execute(f"USE `{name}`")

# Create the cars Table
cursor.execute("CREATE TABLE IF NOT EXISTS cars(\
    id int NOT NULL AUTO_INCREMENT,\
    reg varchar(250),\
    model varchar(250),\
    price int,\
    PRIMARY KEY(id)\
    )") 

# Create the Customer Table
cursor.execute("CREATE TABLE IF NOT EXISTS customer(\
    id int NOT NULL AUTO_INCREMENT,\
    reg varchar(250),\
    name varchar(250),\
    price int,\
    PRIMARY KEY(id)\
    )") 

# Seed only empty tables, with explicitly synthetic records.
for table, columns, rows in [
    ('cars', 'reg, model, price', [('DEMO-001','Skoda Fabia',13000),('DEMO-002','Audi A3',20000)]),
    ('customer','reg, name, price',[('DEMO-001','Sample Customer A',13000),('DEMO-002','Sample Customer B',20000)])]:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(f"INSERT INTO {table} ({columns}) VALUES (%s, %s, %s)", rows)
db.commit()
cursor.close()
db.close()
