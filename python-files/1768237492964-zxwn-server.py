
from flask import Flask, jsonify, request

app = Flask(__name__)

LICENSES = {
    "demo_user": "DEMO"
}

ENDPOINTS = {
    "demo_user": [
        {"name": "PC-01", "status": "Online"},
        {"name": "Laptop-02", "status": "Offline"},
        {"name": "Server-01", "status": "Online"}
    ]
}

@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username")
    if username in LICENSES:
        return jsonify({
            "status": "DEMO",
            "message": "DEMO verzió – PRO fizetés után aktiválható"
        })
    return jsonify({"status": "ERROR", "message": "Nincs licenc"})

@app.route("/endpoints")
def endpoints():
    user = request.args.get("username")
    return jsonify(ENDPOINTS.get(user, []))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
