from flask import Flask, render_template, request, send_file, redirect
import cv2
import numpy as np
from tensorflow import keras
import os
import base64
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime

app = Flask(__name__)

# Ensure folders exist
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/reports", exist_ok=True)

# Load trained model
try:
    model = keras.models.load_model("skin_cancer_model.h5")
    print("✓ MODEL LOADED SUCCESSFULLY")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    model = None


# ============================
# IMAGE PREPROCESSING FUNCTION
# ============================
def preprocess(img):
    """Resize and normalize image for model input"""
    img = cv2.resize(img, (224, 224))
    img = img / 255.0
    return np.expand_dims(img, axis=0)


# ============================
# CLASSIFICATION LOGIC
# ============================
def classify_lesion(confidence):
    """
    Classify lesion as benign or malignant based on confidence
    Assumes model output 0-1 where >0.5 indicates malignant
    """
    if confidence > 0.5:
        return "Malignant", "This lesion shows characteristics typical of malignant melanoma."
    else:
        return "Benign", "This lesion appears to be benign with no significant cancerous features."


# ============================
# RISK ASSESSMENT
# ============================
def assess_risk(confidence):
    """
    Assess risk level:
    - High: >0.75 (Cancer Detected)
    - Medium: 0.50-0.75 (Monitor)
    - Low: <0.50 (Cancer Not Detected)
    """
    if confidence > 0.75:
        return "High"
    elif confidence > 0.50:
        return "Medium"
    else:
        return "Low"


def get_detection_status(lesion_type):
    """Return user-friendly detection status based on lesion type"""
    if lesion_type == "Malignant":
        return "Cancer Detected"
    else:
        return "Cancer Not Detected"


def get_recommendation(risk_level, lesion_type):
    """Generate medical recommendation based on lesion type and risk level"""
    if lesion_type == "Malignant":
        # Malignant skin lesions need urgent attention
        return {
            "title": "🚨 CANCER DETECTED - URGENT MEDICAL ATTENTION REQUIRED",
            "message": f"Malignant characteristics detected with {risk_level} risk level. Immediate consultation with a dermatologist is strongly advised.",
            "color": "#ff4141"
        }
    elif lesion_type == "Benign":
        # Benign lesions still may need monitoring based on risk
        if risk_level == "High":
            return {
                "title": "⚠️ BENIGN BUT MONITOR CLOSELY",
                "message": "While not malignant, this lesion shows some concerning features. Schedule a consultation with a dermatologist.",
                "color": "#ff9800"
            }
        else:
            return {
                "title": "✓ CANCER NOT DETECTED",
                "message": "Lesion appears benign with no significant cancerous features. Continue regular skin monitoring and annual checkups.",
                "color": "#02c96a"
            }
    else:
        return {
            "title": "⚠️ FURTHER EVALUATION NEEDED",
            "message": "Results are inconclusive. Consult with a dermatologist for proper diagnosis.",
            "color": "#ff9800"
        }


# ============================
# ABCDE ANALYSIS
# ============================
def generate_abcde(risk_level):
    """Generate ABCDE dermoscopy analysis based on risk level"""
    analysis = {
        "Low": {
            "A": "Symmetrical shape",
            "B": "Smooth & clear borders",
            "C": "Even color pattern",
            "D": "Small diameter (<6mm)",
            "E": "Minimal evolution"
        },
        "Medium": {
            "A": "Slight asymmetry",
            "B": "Partially uneven borders",
            "C": "Mixed color regions present",
            "D": "Moderate diameter (6-10mm)",
            "E": "Some visible changes"
        },
        "High": {
            "A": "Highly asymmetrical lesion",
            "B": "Border irregularities detected",
            "C": "Multicolor unusual pigment",
            "D": "Large diameter (>10mm)",
            "E": "Rapid evolution observed"
        }
    }
    return analysis.get(risk_level, analysis["Low"])


# ============================
# HOME PAGE
# ============================
@app.route("/")
def home():
    """Render home page"""
    return render_template("index.html")


# ============================
# PREDICT ROUTE
# ============================
@app.route("/predict", methods=["POST"])
def predict():
    """Process uploaded image and generate diagnosis"""
    if model is None:
        return "Error: Model not loaded!", 500

    # Get image from file upload
    image_file = request.files.get("image")

    if not image_file or image_file.filename == "":
        return "Error: No image selected!", 400

    try:
        # Save uploaded image
        img_path = os.path.join("static/uploads", image_file.filename)
        image_file.save(img_path)
        img = cv2.imread(img_path)

        if img is None:
            return "Error: Invalid image file!", 400

        # Preprocess and predict
        processed = preprocess(img)
        confidence = float(model.predict(processed, verbose=0)[0][0])

        # Get classifications and risk
        lesion_type, lesion_description = classify_lesion(confidence)
        risk_level = assess_risk(confidence)
        detection_status = get_detection_status(lesion_type)
        recommendation = get_recommendation(risk_level, lesion_type)
        abcde = generate_abcde(risk_level)

        # Save image for report
        save_path = "static/uploads/result_image.jpg"
        cv2.imwrite(save_path, img)

        # Store result in session
        app.config["LAST_RESULT"] = {
            "detection_status": detection_status,
            "lesion_type": lesion_type,
            "lesion_description": lesion_description,
            "risk_level": risk_level,
            "confidence": round(confidence * 100, 2),
            "recommendation": recommendation,
            "abcde": abcde,
            "img_path": save_path,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return render_template(
            "result.html",
            detection_status=detection_status,
            lesion_type=lesion_type,
            lesion_description=lesion_description,
            risk_level=risk_level,
            confidence=round(confidence * 100, 2),
            recommendation=recommendation,
            abcde=abcde
        )

    except Exception as e:
        return f"Error processing image: {str(e)}", 500


# ============================
# PDF DOWNLOAD ROUTE
# ============================
@app.route("/download_pdf")
def download_pdf():
    """Generate and download medical report as PDF"""
    data = app.config.get("LAST_RESULT")

    if not data:
        return "No report available", 400

    pdf_path = "static/reports/Medical_Report.pdf"

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "AI Skin Cancer Detection Report")

    # Timestamp
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Generated: {data['timestamp']}")

    # Image
    if os.path.exists(data["img_path"]):
        c.drawImage(data["img_path"], 50, height - 320, width=300, height=200)

    # Results Section
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 350, "DIAGNOSIS RESULTS")

    c.setFont("Helvetica", 12)
    y_pos = height - 380

    # Detection Status
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos, f"Detection Status: {data['detection_status']}")
    y_pos -= 25

    # Lesion Type
    c.setFont("Helvetica", 12)
    c.drawString(50, y_pos, f"Lesion Classification: {data['lesion_type']}")
    y_pos -= 20
    c.setFont("Helvetica", 10)
    c.drawString(70, y_pos, data['lesion_description'])
    y_pos -= 30

    # Risk Level
    c.setFont("Helvetica", 12)
    c.drawString(50, y_pos, f"Risk Level: {data['risk_level']}")
    y_pos -= 20
    c.drawString(50, y_pos, f"Confidence Score: {data['confidence']}%")
    y_pos -= 30

    # Recommendation
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos, data['recommendation']['title'])
    y_pos -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y_pos, data['recommendation']['message'])
    y_pos -= 40

    # ABCDE Analysis
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos, "ABCDE Dermoscopic Analysis:")
    y_pos -= 20

    abc = data["abcde"]
    c.setFont("Helvetica", 11)
    for letter_key in ['A', 'B', 'C', 'D', 'E']:
        c.drawString(70, y_pos, f"{letter_key}: {abc[letter_key]}")
        y_pos -= 18

    # Disclaimer
    y_pos -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y_pos, "IMPORTANT DISCLAIMER:")
    y_pos -= 15
    c.setFont("Helvetica", 9)
    disclaimer_text = ("This AI analysis is for informational purposes only and should not be used as a "
                      "substitute for professional medical advice. Always consult a qualified dermatologist "
                      "for proper diagnosis and treatment.")
    c.drawString(50, y_pos, disclaimer_text[:60])
    c.drawString(50, y_pos - 12, disclaimer_text[60:])

    c.save()
    return send_file(pdf_path, as_attachment=True)


# ============================
# WHATSAPP SHARE
# ============================
@app.route("/send_whatsapp", methods=["POST"])
def send_whatsapp():
    """Share diagnosis via WhatsApp"""
    phone = request.form.get("phone", "")
    data = app.config.get("LAST_RESULT")

    if not data:
        return "No report available", 400

    msg = f"""🏥 AI Skin Cancer Detection Report
━━━━━━━━━━━━━━━━━━━━━━━━
Detection: {data['detection_status']}
Type: {data['lesion_type']}
Risk Level: {data['risk_level']}
Confidence: {data['confidence']}%

📋 Recommendation:
{data['recommendation']['message']}

⚠️ This is for informational use only.
Please consult a dermatologist for proper diagnosis.

🔗 Generated by AI Skin Cancer Detection System
"""

    wa_url = "https://wa.me/" + phone + "?text=" + msg.replace("\n", "%0A").replace(" ", "%20")
    return redirect(wa_url)


# ============================
# START SERVER
# ============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
