from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from database import db, User, BackupFile
from license_utils import license_info_message, generate_license_key, validate_license, DEMO_DAYS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///enterprise.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

@app.before_first_request
def create_tables():
    db.create_all()


# -------------------- DASHBOARD --------------------
@app.route('/')
def index():
    users = User.query.all()
    return render_template('dashboard.html', users=users)


# -------------------- LOGIN --------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            return redirect(url_for('user_dashboard', user_id=user.id))
        else:
            flash("User not found!")
    return render_template('login.html')


# -------------------- USER DASHBOARD --------------------
@app.route('/user/<int:user_id>')
def user_dashboard(user_id):
    user = User.query.get_or_404(user_id)
    license_info = license_info_message(user)
    backups = BackupFile.query.filter_by(owner_id=user_id).all()
    return render_template('user_dashboard.html', user=user, license_info=license_info, backups=backups)


# -------------------- FILE UPLOAD --------------------
@app.route('/upload', methods=['POST'])
def upload_file():
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        return "User not found", 404

    file = request.files.get('file')
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        backup = BackupFile(owner_id=user.id,
                            filename=file.filename,
                            stored_path=filepath,
                            uploaded=datetime.utcnow(),
                            size_kb=os.path.getsize(filepath)//1024)
        db.session.add(backup)
        db.session.commit()
        return "File uploaded", 200
    return "No file", 400


# -------------------- LICENSE GENERATION --------------------
@app.route('/generate_license/<int:user_id>')
def generate_license(user_id):
    user = User.query.get_or_404(user_id)
    if user.license_type != "PRO":
        key = generate_license_key(user.id)
        user.license_type = "PRO"
        user.license_start = datetime.utcnow()
        db.session.commit()
        return f"PRO License generated: {key}", 200
    else:
        return "User already PRO", 400


# -------------------- LICENSE VALIDATION --------------------
@app.route('/validate_license/<int:user_id>/<license_key>')
def validate(user_id, license_key):
    user = User.query.get_or_404(user_id)
    if validate_license(user, license_key):
        return "License valid", 200
    else:
        return "Invalid license", 400


# -------------------- RUN SERVER --------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)