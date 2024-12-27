from flask import Flask, jsonify
import sys

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({'statusInstance': 'True'}), 200

@app.route('/process')
def process():
    return jsonify({'idInstance': sys.argv[1]}), 200

@app.route("/")
def index():
    return f"<h1>Порт {sys.argv[1]} работает</h1>"


if __name__ == "__main__":
    app.run(port=int(sys.argv[1]), debug=True)
