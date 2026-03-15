import os
import webbrowser
from customtkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageSequence
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import time
import requests
from io import BytesIO
from itertools import cycle
import pickle
import random
import textwrap
import socket
import re
from datetime import datetime, timedelta
import uuid
import platform
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import sys
import tkinter as tk
import urllib.request, tempfile, os
# Initialize customtkinter
set_appearance_mode("dark")
set_default_color_theme("blue")

# Main application window
root = CTk()
root.title("Shoetax Email Marketing Tool")
root.geometry('750x750')  # Slightly larger to accommodate bigger status box
root.resizable(False, False)

# Set the window icon
try:
    temp_ico = tempfile.NamedTemporaryFile(suffix='.ico', delete=False)
    urllib.request.urlretrieve("https://tempshoetax.netlify.app/shoetaxmain.ico", temp_ico.name)
    root.iconbitmap(temp_ico.name)
    os.unlink(temp_ico.name)  # Delete temp file
except Exception as e:
    print(f"Error: {e}")


PRIMARY_COLOR = "#FF00FF"
BUTTON_HOVER = "#C700C7"
BG_COLOR = "#2B2B2B"
TEXT_COLOR = "white"
FONT_HEADER = ("Orbitron", 24, "bold")
FONT_LABEL = ("Arial", 14)
FONT_ENTRY = ("Arial", 12)
FONT_BUTTON = ("Arial", 13, "bold")

# File for storing emails
EMAILS_FOLDER = "saved_emails"
EMAILS_FILE = os.path.join(EMAILS_FOLDER, "emails.txt")
EMAIL_COUNTER_FILE = os.path.join(EMAILS_FOLDER, "email_counter.dat")

# Global variables
uploaded_emails = []
saved_emails = {}
ad_data = []  # To store ad images and URLs
current_ad_index = 0
ad_popup = None
ad_label = None
popup_position_set = False
email_counter = {}  # To track sent emails per account
last_reset_time = None  # To track when counters were last reset

# Ad data - each tuple contains (image_url, target_url)
AD_DATA = [
    ("https://tempshoetax.netlify.app/image1.jpg", "https://shoetaxtool.com/link1.html"),
    ("https://tempshoetax.netlify.app/image2.jpg", "https://shoetaxtool.com/link2.html"),
    ("https://tempshoetax.netlify.app/image3.jpg", "https://shoetaxtool.com/link3.html"),
]

# Helper function for status updates (now shows only current message)
def update_status(message):
    status_box.configure(state="normal")
    status_box.delete("1.0", "end")  # Clear previous message
    status_box.insert("end", message)  # Insert new message
    status_box.configure(state="disabled")
    root.update_idletasks()  # Force UI update

# Load email counter data
def load_email_counter():
    global email_counter, last_reset_time
    if os.path.exists(EMAIL_COUNTER_FILE):
        try:
            with open(EMAIL_COUNTER_FILE, 'rb') as f:
                data = pickle.load(f)
                email_counter = data.get('counters', {})
                last_reset_time = data.get('last_reset', None)
                
                # Check if 24 hours have passed since last reset
                if last_reset_time and (datetime.now() - last_reset_time) >= timedelta(hours=24):
                    reset_email_counters()
        except:
            email_counter = {}
            last_reset_time = None
    else:
        email_counter = {}
        last_reset_time = None

# Reset all email counters
def reset_email_counters():
    global email_counter, last_reset_time
    email_counter = {}
    last_reset_time = datetime.now()
    save_email_counter()
    update_status("Email counters have been reset (24-hour limit refreshed).")

# Save email counter data
def save_email_counter():
    with open(EMAIL_COUNTER_FILE, 'wb') as f:
        pickle.dump({
            'counters': email_counter,
            'last_reset': last_reset_time
        }, f)

# Check if email can be sent (less than 210 sent)
def can_send_email(gmail):
    # Check if 24 hours have passed since last reset
    if last_reset_time and (datetime.now() - last_reset_time) >= timedelta(hours=24):
        reset_email_counters()
    
    return email_counter.get(gmail, 0) < 210

# Update email counter
def update_email_counter(gmail, count=1):
    if gmail in email_counter:
        email_counter[gmail] += count
    else:
        email_counter[gmail] = count
    
    # Initialize last reset time if not set
    global last_reset_time
    if last_reset_time is None:
        last_reset_time = datetime.now()
    
    save_email_counter()

# Load images from URLs and store with their target URLs
def load_ad_images():
    global ad_data
    ad_data = []
    
    for img_url, target_url in AD_DATA:
        try:
            response = requests.get(img_url)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            ad_data.append((img, target_url))
        except Exception as e:
            print(f"Error loading ad image from {img_url}: {e}")
            # Fallback to a blank image if URL fails
            ad_data.append(Image.new('RGB', (300, 250), target_url))
    

# Show ad popup centered on main window
def show_ad_popup():
    global ad_popup, ad_label, current_ad_index, popup_position_set
    
    if not ad_data:
        load_ad_images()
    
    if not ad_data:
        return
    
    if ad_popup is None or not ad_popup.winfo_exists():
        ad_popup = CTkToplevel(root)
        ad_popup.title("CHECK-OUT ⬇ ")
        ad_popup.attributes('-topmost', True)
        ad_popup.protocol("WM_DELETE_WINDOW", lambda: ad_popup.destroy())
        
        # Set icon for popup window (Windows only)
        try:
            # Create temporary icon file if not exists
            if not os.path.exists("shoetaxlogo.ico"):
                # Convert PNG to ICO if needed
                try:
                    img = Image.open("shoetaxlogo.ico")
                    img.save("shoetaxlogo.ico", format="ICO")
                except:
                    pass
            
            ad_popup.iconbitmap("shoetaxlogo.ico")
        except Exception as e:
            print(f"Error setting popup icon: {e}")
        
        # Get first image dimensions
        img, _ = ad_data[0]
        width, height = img.size
        
        # Set fixed position (slightly offset from center)
        x = root.winfo_x() + (root.winfo_width() // 2) - (width // 2)
        y = root.winfo_y() + (root.winfo_height() // 2) - (height // 2)
        popup_position_set = True
        
        # Make the entire label clickable
        ad_label = CTkLabel(ad_popup, text="", cursor="hand2")
        ad_label.pack()
        
        # Start the ad rotation
        rotate_ads()
    else:
        ad_popup.lift()

# Rotate ads automatically
def rotate_ads():
    global current_ad_index, popup_position_set
    
    if ad_popup is None or not ad_popup.winfo_exists():
        return
    
    if not ad_data:
        return
    
    # Get current image and URL
    img, target_url = ad_data[current_ad_index]
    
    # Convert PIL Image to CTkImage
    ctk_img = CTkImage(light_image=img, size=img.size)
    
    # Update label with new image
    ad_label.configure(image=ctk_img)
    ad_label.image = ctk_img  # Keep reference
    
    # Remove previous click binding and add new one
    ad_label.unbind("<Button-1>")
    ad_label.bind("<Button-1>", lambda e: webbrowser.open(target_url))
    
    # Keep popup in the same position (don't resize or reposition)
    if not popup_position_set:
        width, height = img.size
        x = root.winfo_x() + (root.winfo_width() // 2) - (width // 2)
        y = root.winfo_y() + (root.winfo_height() // 2) - (height // 2)
        ad_popup.geometry(f"{width}x{height}+{x}+{y}")
        popup_position_set = True
    
    # Increment index (cycle back to 0 if at end)
    current_ad_index = (current_ad_index + 1) % len(ad_data)
    
    # Schedule next rotation (every 3 seconds)
    ad_popup.after(3000, rotate_ads)

# Ensure the folder and file exist
def ensure_email_storage():
    if not os.path.exists(EMAILS_FOLDER):
        os.makedirs(EMAILS_FOLDER)
    if not os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, "w") as file:
            file.write("")

# Load saved emails from file
def load_saved_emails():
    global saved_emails
    saved_emails.clear()
    ensure_email_storage()
    with open(EMAILS_FILE, "r") as file:
        for line in file:
            email, password = line.strip().split("||")
            saved_emails[email] = password

# Save emails to file
def save_emails_to_file():
    with open(EMAILS_FILE, "w") as file:
        for email, password in saved_emails.items():
            file.write(f"{email}||{password}\n")

# Refresh the email dropdown
def refresh_email_dropdown():
    email_menu.configure(values=list(saved_emails.keys()))
    email_var.set("")  # Reset dropdown

# Select email from dropdown
def select_email(email):
    if email in saved_emails:
        email_var.set(email)
        gmail_entry.delete(0, "end")
        gmail_entry.insert(0, email)
        password_entry.delete(0, "end")
        password_entry.insert(0, saved_emails[email])

# Add email and app password
def add_email():
    gmail = gmail_entry.get().strip()
    password = password_entry.get().strip()

    if not gmail or not password:
        messagebox.showwarning("Warning", "Please enter both email and app password.")
        return

    saved_emails[gmail] = password
    save_emails_to_file()
    update_status(f"Added email: {gmail}")
    refresh_email_dropdown()
    gmail_entry.delete(0, "end")
    password_entry.delete(0, "end")

# Upload email list
def upload_email_list():
    global uploaded_emails
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        try:
            with open(file_path, "r") as file:
                uploaded_emails = [line.strip() for line in file if line.strip()]
                update_status(f"Uploaded {len(uploaded_emails)} emails successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload email list: {e}")

# Validate email format
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Clean email list
def clean_email_list(emails):
    return [email.strip().lower() for email in emails if is_valid_email(email.strip())]

# Randomize delay between emails
def get_random_delay():
    return random.randint(15, 30)  # 15-30 seconds between emails

# Create personalized email content
def personalize_email(body, recipient):
    # Simple personalization - add recipient's name if available
    name = recipient.split('@')[0]
    personalized_body = body.replace("{name}", name.capitalize())
    return personalized_body

# Create email headers with anti-spam measures
def create_email_headers(gmail, recipient, subject):
    msg = MIMEMultipart()
    msg['From'] = gmail
    msg['To'] = recipient
    msg['Subject'] = subject
    
    # Anti-spam headers
    msg['X-Mailer'] = "ShoeTax Email Tool"
    msg['X-Priority'] = "3"  # Normal priority
    msg['X-MSMail-Priority'] = "Normal"
    msg['X-Unsent'] = "1"
    
    return msg

# Sending emails with delay
def start_sending_emails():
    if not uploaded_emails:
        update_status("No email list uploaded. Please upload an email list first.")
        return
    threading.Thread(target=send_emails_with_delay).start()

def send_emails_with_delay():
    gmail = gmail_entry.get().strip()
    password = password_entry.get().strip()
    subject = subject_entry.get().strip()
    body = email_body.get("1.0", "end").strip()

    if not gmail or not password or not subject or not body:
        update_status("Please fill in all fields before sending emails.")
        return

    # Check email limit
    if not can_send_email(gmail):
        update_status(f"⚠️ You have reached the 210 email limit for {gmail}. Please wait 24 hours or use another Gmail account.")
        return
    
    remaining_emails = 210 - email_counter.get(gmail, 0)
    if len(uploaded_emails) + 1 > remaining_emails:  # +1 for the sender's email
        update_status(f"⚠️ You can only send {remaining_emails} more emails with {gmail} (210 limit).")
        return

    # Clean and validate email list
    clean_emails = clean_email_list(uploaded_emails)
    if len(clean_emails) < len(uploaded_emails):
        update_status(f"Removed {len(uploaded_emails) - len(clean_emails)} invalid emails from list.")

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(gmail, password)

        # FIRST send email to the sender's own address
        try:
            msg = create_email_headers(gmail, gmail, f"[FROM SHOETAX] {subject}")
            
            # HTML content for the self-test email
            self_body = """<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Campaign Processing | Shoetax</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">

</head>
<body>
    <div class="container">
        <div class="confirmation-card">
            <div class="header">
                <img src="https://cdn-icons-png.flaticon.com/512/2583/2583344.png" alt="icon" class="floating-shoe shoe-1">
                <h1>Your Email Campaign is Being Processed</h1>
                <p>We're delivering your message to subscribers with care</p>
                <img src="https://cdn-icons-png.flaticon.com/512/2583/2583315.png" alt="icon" class="floating-shoe shoe-2">
            </div>
            
            <div class="progress-container">
                <div class="status-message">
                    Our system is working hard to send your emails. This process may take some time depending on your list size.
                </div>
            
            <div class="blog-section">
                <h2>While You Wait, CHECK OUT!!</h2>
                <div class="blog-grid">
                    <a href="https://shoetaxtool.com/link1.html" target="_blank" class="blog-card">
                        <img src="https://tempshoetax.netlify.app/image1.jpg" alt="click-here" class="blog-image">
                    </a>
                    
                    <a href="https://shoetaxtool.com/link2.htm" target="_blank" class="blog-card">
                        <img src="https://tempshoetax.netlify.app/image2.jpg" alt="click-here" class="blog-image">

                    </a>
                    
                    <a href="https://shoetaxtool.com/link3.html" target="_blank" class="blog-card">
                        <img src="https://tempshoetax.netlify.app/image3.jpg" alt="click-here" class="blog-image">
                    </a>
                </div>
            </div>
            
        </div>
    </div>
</body>
</html>"""
            
            msg.attach(MIMEText(self_body, 'html'))
            server.sendmail(gmail, gmail, msg.as_string())
            update_email_counter(gmail)
            update_status(f"Conformation email sent to {gmail} (Total sent: {email_counter.get(gmail, 0)}/210).")
            time.sleep(5)  # Short delay before sending to recipients
        except Exception as e:
            update_status(f"Failed to send self-test email: {e}")

        # THEN send to all recipients
        for index, recipient in enumerate(clean_emails, start=1):
            try:
                # Create personalized email
                personalized_body = personalize_email(body, recipient)
                
                # Add plain text watermark to email body
                watermark = """

                                                              
 Sent using https://shoetaxtool.com               
                                                              

"""
                personalized_body += watermark  # Append the plain text watermark
                
                msg = create_email_headers(gmail, recipient, subject)
                
                # Use plain text instead of HTML for better deliverability
                msg.attach(MIMEText(personalized_body, 'plain'))

                server.sendmail(gmail, recipient, msg.as_string())
                update_email_counter(gmail)
                update_status(f"Email {index}/{len(clean_emails)} sent to {recipient} (Total sent: {email_counter.get(gmail, 0)}/210).")
                
                # Random delay between emails
                delay = get_random_delay()
                time.sleep(delay)
                
            except Exception as e:
                update_status(f"Failed to send email to {recipient}: {e}")

        server.quit()
        update_status(f"All emails sent successfully! Total sent from {gmail}: {email_counter.get(gmail, 0)}/210")
    except smtplib.SMTPAuthenticationError:
        update_status("Authentication failed. Check your Gmail and App Password.")
    except Exception as e:
        update_status(f"Failed to send emails: {e}")

# Open blogs website
def open_blogs():
    webbrowser.open("https://shoetaxtool.com/blogs")

# Social media link functions
def open_instagram():
    webbrowser.open("https://www.instagram.com/shoetaxtool")

def open_telegram():
    webbrowser.open("https://telegram.org")

def open_website():
    webbrowser.open("https://www.vaipar.online")

def rate_us():
    webbrowser.open("https://example.com/rate")  # Replace with your actual rating URL

# UI Setup
header = CTkFrame(root, fg_color=PRIMARY_COLOR, corner_radius=0)
header.pack(fill="x", pady=5)

# Load and set the logo image
try:
    # Download the logo image from the URL
    response = requests.get("https://dummyshoetax.netlify.app/shoetaxlogo.png")
    logo_img = Image.open(BytesIO(response.content))
    logo_image = CTkImage(light_image=logo_img, size=(60, 60))
except Exception as e:
    print(f"Error loading logo image: {e}")
    # Fallback if logo image not found
    logo_image = None

header_label = CTkLabel(header, image=logo_image, text="")  # Remove text, set image
header_label.grid(row=0, column=1, pady=10)

# Center the logo
header.grid_columnconfigure(1, weight=1)

# Input fields
input_frame = CTkFrame(root, fg_color=BG_COLOR, corner_radius=15)
input_frame.pack(padx=20, pady=20, fill="x")

CTkLabel(input_frame, text="📧", text_color=TEXT_COLOR, font=FONT_LABEL).grid(row=0, column=0, sticky="w", padx=15, pady=15)
gmail_entry = CTkEntry(input_frame, placeholder_text="Enter your Gmail", font=FONT_ENTRY, width=300, corner_radius=10)
gmail_entry.grid(row=0, column=1, padx=10, pady=10)

CTkLabel(input_frame, text="🗝", text_color=TEXT_COLOR, font=FONT_LABEL).grid(row=1, column=0, sticky="w", padx=10, pady=10)
password_entry = CTkEntry(input_frame, placeholder_text="Enter app password", font=FONT_ENTRY, width=300, show="*", corner_radius=10)
password_entry.grid(row=1, column=1, padx=10, pady=10)

CTkLabel(input_frame, text="📝", text_color=TEXT_COLOR, font=FONT_LABEL).grid(row=2, column=0, sticky="w", padx=10, pady=10)
subject_entry = CTkEntry(input_frame, placeholder_text="Enter email subject", font=FONT_ENTRY, width=300, corner_radius=10)
subject_entry.grid(row=2, column=1, padx=10, pady=10)

# Email dropdown
CTkLabel(input_frame, text="📂", text_color=TEXT_COLOR, font=FONT_LABEL).grid(row=3, column=0, sticky="w", padx=10, pady=10)
email_var = StringVar(value="")
email_menu = CTkOptionMenu(input_frame, variable=email_var, values=[], command=select_email, width=300, corner_radius=10)
email_menu.grid(row=3, column=1, padx=10, pady=10)

# Frame for email body section
email_body_frame = CTkFrame(root, fg_color="transparent")
email_body_frame.pack(padx=20, pady=(0, 10), fill="x")

# Email body label
CTkLabel(email_body_frame, text="📜", text_color=TEXT_COLOR, font=FONT_LABEL).pack(anchor="w", padx=(0, 0), pady=(0, 5))

# Frame for email body and social icons
body_content_frame = CTkFrame(email_body_frame, fg_color="transparent")
body_content_frame.pack(fill="x")

# Email body (keeping original size - 600px width)
email_body = CTkTextbox(body_content_frame, font=FONT_ENTRY, width=600, height=150, border_width=2, border_color=PRIMARY_COLOR, corner_radius=10)
email_body.pack(side="left", padx=(0, 10))

# Social Media Icons Frame (placed to the right of email body)
social_frame = CTkFrame(body_content_frame, fg_color="transparent", width=100)
social_frame.pack(side="right", fill="y")

# Load social media icons (using placeholder images - replace with your actual image paths)
try:
    # Download Instagram icon
    insta_response = requests.get("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Instagram_logo_2016.svg/768px-Instagram_logo_2016.svg.png")
    insta_img = Image.open(BytesIO(insta_response.content))
    insta_img = CTkImage(light_image=insta_img, size=(30, 30))
except Exception as e:
    print(f"Error loading social icons: {e}")
    insta_img = None

# Create the buttons using images
insta_btn = CTkButton(social_frame, image=insta_img, text="", width=45, height=45, 
                     fg_color="transparent", hover_color="#333333", command=open_instagram, corner_radius=10)

# Place buttons in the frame vertically
insta_btn.pack(pady=5)

# Centered button frame with equal gaps between the buttons
button_frame = CTkFrame(root, fg_color=BG_COLOR, corner_radius=15)
button_frame.pack(padx=20, pady=20, fill="x")

# Create an equal gap between buttons using grid configuration
button_frame.grid_columnconfigure(0, weight=1)
button_frame.grid_columnconfigure(1, weight=1)
button_frame.grid_columnconfigure(2, weight=1)
button_frame.grid_columnconfigure(3, weight=1)

FONT_BUTTON = ("Roboto", 12, "bold")  # Slightly bigger & bold for a premium feel  

CTkButton(button_frame, text="Add Email", command=add_email, fg_color=PRIMARY_COLOR, hover_color=BUTTON_HOVER, font=FONT_BUTTON, corner_radius=10).grid(row=0, column=0, padx=10, pady=10)
CTkButton(button_frame, text="Upload Email List", command=upload_email_list, fg_color=PRIMARY_COLOR, hover_color=BUTTON_HOVER, font=FONT_BUTTON, corner_radius=10).grid(row=0, column=1, padx=10, pady=10)
CTkButton(button_frame, text="Send Emails", command=start_sending_emails, fg_color=PRIMARY_COLOR, hover_color=BUTTON_HOVER, font=FONT_BUTTON, corner_radius=10).grid(row=0, column=2, padx=10, pady=10)
CTkButton(button_frame, text="Blogs", command=open_blogs, fg_color=PRIMARY_COLOR, hover_color=BUTTON_HOVER, font=FONT_BUTTON, corner_radius=10).grid(row=0, column=3, padx=10, pady=10)

# Status box - now shows only the latest message
CTkLabel(root, text="📊", text_color=TEXT_COLOR, font=FONT_LABEL).pack(anchor="w", padx=25)
status_box = CTkTextbox(root, font=FONT_ENTRY, width=700, height=40, border_width=2, border_color=PRIMARY_COLOR, corner_radius=10)
status_box.pack(padx=25, pady=10)
status_box.configure(state="disabled")

# Load existing emails and counters on startup
ensure_email_storage()
load_saved_emails()
load_email_counter()
refresh_email_dropdown()

# Load ad images and show popup after a delay
root.after(3000, load_ad_images)  
root.after(20000, show_ad_popup)
root.after(300000, show_ad_popup)
root.after(600000, show_ad_popup)
root.after(3000000, show_ad_popup)



root.mainloop()
