from flask import Flask, request, jsonify
import io
import logging
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import os
import sys
import base64

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ===== CONFIGURATION =====
# Set Tesseract path if not in system PATH (Windows example)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# =========================

def preprocess_image(image):
    """Enhance image for better OCR accuracy"""
    # Convert to grayscale
    image = image.convert('L')
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)
    # Apply sharpen filter
    image = image.filter(ImageFilter.SHARPEN)
    return image

@app.route('/CaptchaAPI', methods=['POST'])
def solve_captcha():
    """Endpoint called by phbot plugin"""
    # Validate request
    if not request.is_json:
        app.logger.error("Request is not JSON")
        return jsonify({'success': False, 'message': 'Request must be JSON'}), 400

    data = request.get_json()
    if not data or 'data' not in data:
        app.logger.error("Missing 'data' field in JSON")
        return jsonify({'success': False, 'message': 'Missing data field'}), 400

    hex_data = data['data']
    app.logger.info(f"Received captcha data (hex length: {len(hex_data)})")

    try:
        # Convert hex to bytes
        image_bytes = bytes.fromhex(hex_data)

        # Open image from memory
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            app.logger.error(f"Failed to open image: {e}")
            return jsonify({'success': False, 'message': 'Invalid image data'}), 400

        # Preprocess image for better OCR
        processed_image = preprocess_image(image)

        # Extract text using Tesseract
        # psm 8 = single line of text
        custom_config = r'--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        captcha_text = pytesseract.image_to_string(processed_image, config=custom_config).strip()

        app.logger.info(f"OCR extracted: '{captcha_text}'")

        # Verify text is not empty
        if not captcha_text:
            # Second attempt without preprocessing
            captcha_text = pytesseract.image_to_string(image, config='--psm 8').strip()
            app.logger.info(f"Second attempt (no preprocessing): '{captcha_text}'")

        if captcha_text:
            return jsonify({'success': True, 'captcha': captcha_text})
        else:
            app.logger.warning("No text found in captcha")
            return jsonify({'success': False, 'message': 'No text found'}), 400

    except Exception as e:
        app.logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return "Captcha Server for phbot is running. Use POST /CaptchaAPI with JSON data."

if __name__ == '__main__':
    # Run server on localhost:15999
    # debug=False to avoid double restart
    app.run(host='127.0.0.1', port=15999, debug=False)