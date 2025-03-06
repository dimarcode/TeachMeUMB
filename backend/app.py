import mysql.connector
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Flask is Running! 🚀"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

@app.route('/db-test')
def db_test():
    try:
        # Example code to test MySQL connection
        import mysql.connector
        conn = mysql.connector.connect(
            host='mysql',  # Service name in Docker Compose
            user='root',  # Username set in the environment
            password='hunter2',  # Password set in the environment
            database='database'  # Database name set in the environment
        )
        return jsonify({"message": "MySQL connection successful!"})
    except Exception as e:
        return jsonify({"error": str(e)})