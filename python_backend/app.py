from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def hello():
    return jsonify({"message": "Hello from your Python backend!"})

@app.route("/data")
def data():
    return jsonify({"value": 42})
