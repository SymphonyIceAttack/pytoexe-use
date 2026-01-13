from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route("/")
def index():
    return "Document Analyzer DEMO - Limited Access\nUpgrade to PRO for full features."

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    text = data.get("text", "")
    # DEMO csak visszaküld rövid statisztikát
    word_count = len(text.split())
    return jsonify({
        "word_count": word_count,
        "message": "DEMO version - Upgrade to PRO for full analysis"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)