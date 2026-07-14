import os
import mysql.connector

print("========== DATABASE VARIABLES ==========")
print("MYSQLHOST =", os.getenv("MYSQLHOST"))
print("MYSQLPORT =", os.getenv("MYSQLPORT"))
print("MYSQLDATABASE =", os.getenv("MYSQLDATABASE"))
print("MYSQLUSER =", os.getenv("MYSQLUSER"))
print("========================================")

try:
    connection = mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        port=int(os.getenv("MYSQLPORT", 3306)),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE")
    )

    print("✅ Connected to MySQL successfully!")

    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT DATABASE();")
    current_db = cursor.fetchone()

    print("Current Database:", current_db)

except Exception as e:
    print("❌ Database Connection Error")
    print(e)
    raise