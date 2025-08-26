from flask import Flask
import mysql.connector


app = Flask(__name__)
app.secret_key = "test_123"

mydb = mysql.connector.connect(
      host="localhost",
      user="root",
      password="root",
      database="society"
)
cursor = mydb.cursor()

from app.module import demo 