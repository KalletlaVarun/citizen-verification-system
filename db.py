import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_PASSWORD",
    database="smart_verification_system"
)

cursor = connection.cursor(dictionary=True)