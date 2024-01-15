from flask import Flask
from flask_pymongo import PyMongo

app = Flask(__name__)
app.secret_key = 'temp_secret_key'
app.config["MONGO_URI"] = "mongodb://mongo:27017/projectDb"
mongo = PyMongo(app)
