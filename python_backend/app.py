from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def root():
    return jsonify({"message": "Hello from Python backend!"})

@app.route("/data")
def data():
    return jsonify({"value": 42})

