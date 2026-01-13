from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from dateutil import parser

db = SQLAlchemy()

# -------- Felhasználók --------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    # DEMO PRO licence napjaihoz
    license_start = db.Column(db.DateTime, nullable=True)
    license_type = db.Column(db.String(20), default="DEMO")  # DEMO / PRO

    def license_days_left(self, demo_days):
        if self.license_type == "PRO":
            return 999999  # PRO nem jár le
        if not self.license_start:
            return demo_days
        now = datetime.utcnow()
        delta = now - self.license_start
        remaining = demo_days - delta.days
        return max(0, remaining)

# -------- Feltöltött mentések --------
class BackupFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(200))
    stored_path = db.Column(db.String(500))
    uploaded = db.Column(db.DateTime, default=datetime.utcnow)
    size_kb = db.Column(db.Integer)

    user = db.relationship("User", backref="backups")