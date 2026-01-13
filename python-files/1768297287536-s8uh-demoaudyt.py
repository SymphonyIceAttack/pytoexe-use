from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def index():
    return "Cybersecurity Audit DEMO - Limited Access\nUpgrade to PRO for full audit."

@app.route("/scan")
def scan():
    # Szimulált hálózati eszközök
    devices = [
        {"name": "Router-1", "status": "Online"},
        {"name": "Switch-1", "status": "Offline"},
        {"name": "Server-1", "status": "Online"}
    ]
    vulnerabilities = [
        {"device": "Switch-1", "issue": "Old firmware"},
        {"device": "Server-1", "issue": "Open port 22"}
    ]
    return jsonify({
        "devices": devices,
        "vulnerabilities": vulnerabilities,
        "message": "DEMO scan - Upgrade to PRO for full network audit"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010)