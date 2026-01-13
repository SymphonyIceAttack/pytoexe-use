from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def index():
    return "Network Monitoring DEMO - Limited Access\nUpgrade to PRO for full monitoring."

@app.route("/status")
def status():
    # DEMO: csak szimulált hálózati állapot
    network_devices = [
        {"name": "Router-1", "status": "Online"},
        {"name": "Switch-1", "status": "Offline"}
    ]
    return jsonify({
        "devices": network_devices,
        "message": "DEMO version - Upgrade to PRO for full network monitoring"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006)