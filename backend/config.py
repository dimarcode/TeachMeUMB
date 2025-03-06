from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Update the DATABASE URI to use MySQL (not SQLite)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:hunter2@mysql/database"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)