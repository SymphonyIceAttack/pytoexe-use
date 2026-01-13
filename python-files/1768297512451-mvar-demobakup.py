from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def index():
    return "Backup Automation DEMO - Limited Access\nUpgrade to PRO for full features."

@app.route("/backup")
def backup():
    # DEMO csak jelzi a mentést
    return jsonify({
        "status": "Demo backup completed (simulated)",
        "message": "DEMO version - Upgrade to PRO for real backups"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)