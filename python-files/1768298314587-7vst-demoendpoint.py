from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def index():
    return "Endpoint Manager DEMO - Limited Access\nUpgrade to PRO for full features."

@app.route("/status")
def status():
    # DEMO csak például 2 gép állapotát mutatja
    endpoints = [
        {"name": "Workstation-1", "status": "Online"},
        {"name": "Workstation-2", "status": "Offline"}
    ]
    return jsonify({
        "endpoints": endpoints,
        "message": "DEMO version - Upgrade to PRO for full monitoring"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)