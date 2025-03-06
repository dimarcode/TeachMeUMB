from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Update the DATABASE URI to use MySQL (not SQLite)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:hunter2@mysql/database"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

@app.route('/')
def home():
    return jsonify({"message": "Flask is Running! 🚀"})

@app.route('/db-test')
def db_test():
    try:
        # Test the database connection using SQLAlchemy
        result = db.session.execute(text("SELECT 1"))
        return jsonify({"message": "MySQL connection successful!", "result": result.fetchone()})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)