from flask import Flask, request, jsonify

app = Flask(__name__)

VALID_LICENSES = {
    "LIC-2026-AAA": "FERNET_KULCS_IDE",
}

@app.route("/api/check_license", methods=["POST"])
def check():
    lic = request.json.get("license")
    if lic in VALID_LICENSES:
        return jsonify({"decrypt_key": VALID_LICENSES[lic]})
    return jsonify({"error": "invalid"}), 403

app.run(host="0.0.0.0", port=8080)