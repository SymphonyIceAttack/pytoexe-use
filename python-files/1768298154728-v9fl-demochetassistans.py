from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route("/")
def index():
    return "AI Chat Assistant DEMO - Limited Access\nUpgrade to PRO for full features."

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    # DEMO: egyszerű válasz, nem AI logika
    reply = f"DEMO reply: I received your message: '{user_message}'"
    return jsonify({"reply": reply, "message": "DEMO version - Upgrade to PRO for AI responses"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)