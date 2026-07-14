import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="smart_verification_system"
)

cursor = connection.cursor(dictionary=True)