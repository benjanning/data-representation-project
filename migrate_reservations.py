"""Add reservation storage without replacing or reseeding existing records."""

if __name__ == "__main__":
    import mysql.connector
    import dbconfig
    from rental_mysql import migrate

    connection = mysql.connector.connect(**dbconfig.mysql)
    try:
        migrate(connection)
    finally:
        connection.close()
    print("Reservation table is ready; existing records were preserved.")
