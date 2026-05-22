import sqlite3
import csv
import io
import os
import webbrowser
import threading
from datetime import datetime, date, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, g
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mitarbeiter-geheim-schluessel-2024")

DATABASE = os.path.join(os.path.dirname(__file__), "mitarbeiter.db")


# ---------------------------------------------------------------------------
# Datenbank
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS mitarbeiter (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            dienstnummer TEXT UNIQUE NOT NULL,
            vorname     TEXT NOT NULL,
            nachname    TEXT NOT NULL,
            telefon     TEXT DEFAULT '',
            team        TEXT NOT NULL,
            fuehrerschein TEXT,
            d95         TEXT,
            fahrerkarte TEXT,
            sachbezug   TEXT NOT NULL DEFAULT 'NEIN',
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rolle    TEXT NOT NULL DEFAULT 'mitarbeiter'
        );
    """)
    cur = db.execute("SELECT COUNT(*) as n FROM users WHERE username='admin'")
    if cur.fetchone()["n"] == 0:
        db.execute(
            "INSERT INTO users (username, password, rolle) VALUES (?, ?, ?)",
            ("admin", "admin123", "admin")
        )
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def parse_date_de(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


def cert_color(date_str):
    d = parse_date_de(date_str)
    if d is None:
        return ""
    today = date.today()
    diff = (d - today).days
    if diff < 0:
        return "red"
    if diff <= 30:
        return "orange"
    return "green"


def cert_status(date_str):
    d = parse_date_de(date_str)
    if d is None:
        return "none"
    today = date.today()
    diff = (d - today).days
    if diff < 0:
        return "expired"
    if diff <= 30:
        return "warning"
    return "ok"


app.jinja_env.globals["cert_color"] = cert_color
app.jinja_env.globals["cert_status"] = cert_status
app.jinja_env.globals["today"] = date.today


# ---------------------------------------------------------------------------
# Auth-Decorators
# ---------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Bitte zuerst anmelden.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def edit_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        rolle = session.get("rolle")
        if rolle not in ("admin", "teamleiter"):
            flash("Keine Berechtigung.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("rolle") != "admin":
            flash("Nur für Administratoren.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Routen
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    db = get_db()
    search = request.args.get("q", "").strip()
    if search:
        pattern = f"%{search}%"
        rows = db.execute(
            """SELECT * FROM mitarbeiter
               WHERE dienstnummer LIKE ? OR vorname LIKE ? OR nachname LIKE ?
                  OR telefon LIKE ? OR team LIKE ?
               ORDER BY nachname""",
            (pattern, pattern, pattern, pattern, pattern)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM mitarbeiter ORDER BY nachname"
        ).fetchall()
    return render_template("index.html", mitarbeiter=rows, search=search)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
        if user and user["password"] == password:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["rolle"] = user["rolle"]
            return redirect(url_for("dashboard"))
        flash("Benutzername oder Passwort falsch.", "danger")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    rows = db.execute("SELECT * FROM mitarbeiter").fetchall()
    today = date.today()

    total = len(rows)
    sachbezug_count = sum(1 for r in rows if r["sachbezug"] == "JA")

    teams = {}
    for r in rows:
        teams[r["team"]] = teams.get(r["team"], 0) + 1

    def check_certs(row):
        issues = []
        for col in ("fuehrerschein", "d95", "fahrerkarte"):
            s = cert_status(row[col])
            if s in ("expired", "warning"):
                issues.append((col, row[col], s))
        return issues

    cert_issues = []
    for r in rows:
        issues = check_certs(r)
        if issues:
            cert_issues.append((r, issues))

    expired_count = sum(
        1 for r in rows
        for col in ("fuehrerschein", "d95", "fahrerkarte")
        if cert_status(r[col]) == "expired"
    )
    warning_count = sum(
        1 for r in rows
        for col in ("fuehrerschein", "d95", "fahrerkarte")
        if cert_status(r[col]) == "warning"
    )

    return render_template(
        "dashboard.html",
        total=total,
        sachbezug_count=sachbezug_count,
        teams=teams,
        cert_issues=cert_issues,
        expired_count=expired_count,
        warning_count=warning_count,
    )


@app.route("/mitarbeiter/neu", methods=["GET", "POST"])
@login_required
@edit_required
def mitarbeiter_neu():
    if request.method == "POST":
        db = get_db()
        try:
            db.execute(
                """INSERT INTO mitarbeiter
                   (dienstnummer, vorname, nachname, telefon, team,
                    fuehrerschein, d95, fahrerkarte, sachbezug)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    request.form["dienstnummer"].strip(),
                    request.form["vorname"].strip(),
                    request.form["nachname"].strip(),
                    request.form.get("telefon", "").strip(),
                    request.form["team"].strip(),
                    request.form.get("fuehrerschein", "").strip() or None,
                    request.form.get("d95", "").strip() or None,
                    request.form.get("fahrerkarte", "").strip() or None,
                    request.form.get("sachbezug", "NEIN"),
                )
            )
            db.commit()
            flash("Mitarbeiter wurde angelegt.", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash("Dienstnummer bereits vorhanden.", "danger")
    return render_template("mitarbeiter_detail.html", m=None)


@app.route("/mitarbeiter/<int:mid>/bearbeiten", methods=["GET", "POST"])
@login_required
@edit_required
def mitarbeiter_edit(mid):
    db = get_db()
    m = db.execute("SELECT * FROM mitarbeiter WHERE id=?", (mid,)).fetchone()
    if not m:
        flash("Mitarbeiter nicht gefunden.", "danger")
        return redirect(url_for("index"))
    if request.method == "POST":
        try:
            db.execute(
                """UPDATE mitarbeiter SET
                   dienstnummer=?, vorname=?, nachname=?, telefon=?, team=?,
                   fuehrerschein=?, d95=?, fahrerkarte=?, sachbezug=?
                   WHERE id=?""",
                (
                    request.form["dienstnummer"].strip(),
                    request.form["vorname"].strip(),
                    request.form["nachname"].strip(),
                    request.form.get("telefon", "").strip(),
                    request.form["team"].strip(),
                    request.form.get("fuehrerschein", "").strip() or None,
                    request.form.get("d95", "").strip() or None,
                    request.form.get("fahrerkarte", "").strip() or None,
                    request.form.get("sachbezug", "NEIN"),
                    mid,
                )
            )
            db.commit()
            flash("Änderungen gespeichert.", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash("Dienstnummer bereits vorhanden.", "danger")
    return render_template("mitarbeiter_detail.html", m=m)


@app.route("/mitarbeiter/<int:mid>/loeschen", methods=["POST"])
@login_required
@edit_required
def mitarbeiter_loeschen(mid):
    db = get_db()
    db.execute("DELETE FROM mitarbeiter WHERE id=?", (mid,))
    db.commit()
    flash("Mitarbeiter wurde gelöscht.", "success")
    return redirect(url_for("index"))


@app.route("/import", methods=["GET", "POST"])
@login_required
@edit_required
def csv_import():
    preview = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "preview":
            file = request.files.get("file")
            if not file or not file.filename:
                flash("Bitte eine CSV-Datei auswählen.", "danger")
                return render_template("import.html", preview=None)
            content = file.read().decode("utf-8-sig", errors="replace")
            reader = csv.DictReader(io.StringIO(content), delimiter=";")
            rows = list(reader)
            return render_template("import.html", preview=rows, raw=content)

        elif action == "confirm":
            raw = request.form.get("raw", "")
            reader = csv.DictReader(io.StringIO(raw), delimiter=";")
            db = get_db()
            imported = skipped = 0
            for row in reader:
                try:
                    db.execute(
                        """INSERT INTO mitarbeiter
                           (dienstnummer, vorname, nachname, telefon, team,
                            fuehrerschein, d95, fahrerkarte, sachbezug)
                           VALUES (?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(dienstnummer) DO UPDATE SET
                           vorname=excluded.vorname, nachname=excluded.nachname,
                           telefon=excluded.telefon, team=excluded.team,
                           fuehrerschein=excluded.fuehrerschein,
                           d95=excluded.d95, fahrerkarte=excluded.fahrerkarte,
                           sachbezug=excluded.sachbezug""",
                        (
                            row.get("dienstnummer", "").strip(),
                            row.get("vorname", "").strip(),
                            row.get("nachname", "").strip(),
                            row.get("telefon", "").strip(),
                            row.get("team", "").strip(),
                            row.get("fuehrerschein", "").strip() or None,
                            row.get("d95", "").strip() or None,
                            row.get("fahrerkarte", "").strip() or None,
                            row.get("sachbezug", "NEIN").strip(),
                        )
                    )
                    imported += 1
                except Exception:
                    skipped += 1
            db.commit()
            flash(f"{imported} importiert, {skipped} übersprungen.", "success")
            return redirect(url_for("index"))

    return render_template("import.html", preview=None)


@app.route("/benutzer")
@login_required
@admin_required
def users():
    db = get_db()
    rows = db.execute("SELECT * FROM users ORDER BY username").fetchall()
    return render_template("users.html", users=rows)


@app.route("/benutzer/neu", methods=["POST"])
@login_required
@admin_required
def users_neu():
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password, rolle) VALUES (?,?,?)",
            (
                request.form["username"].strip(),
                request.form["password"],
                request.form.get("rolle", "mitarbeiter"),
            )
        )
        db.commit()
        flash("Benutzer angelegt.", "success")
    except sqlite3.IntegrityError:
        flash("Benutzername bereits vorhanden.", "danger")
    return redirect(url_for("users"))


@app.route("/benutzer/<int:uid>/loeschen", methods=["POST"])
@login_required
@admin_required
def users_loeschen(uid):
    if uid == session.get("user_id"):
        flash("Sie können sich nicht selbst löschen.", "danger")
        return redirect(url_for("users"))
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (uid,))
    db.commit()
    flash("Benutzer gelöscht.", "success")
    return redirect(url_for("users"))


# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    url = f"http://localhost:{port}"
    print(f"\n{'='*50}")
    print(f"  Mitarbeiter Verwaltung")
    print(f"  Adresse: {url}")
    print(f"  Login: admin / admin123")
    print(f"{'='*50}\n")

    def open_browser():
        import time
        time.sleep(1.2)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="0.0.0.0", port=port, debug=False)
