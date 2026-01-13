from datetime import datetime, timedelta
import json

# Betöltjük a configot (IBAN, email, telefon, demo napok)
with open("config.json", "r") as f:
    CONFIG = json.load(f)

IBAN = CONFIG.get("iban")
EMAIL = CONFIG.get("email")
PHONE = CONFIG.get("phone")
DEMO_DAYS = CONFIG.get("demo_days", 7)


def is_pro(user):
    """
    Ellenőrzi, hogy a felhasználó PRO licenccel rendelkezik-e
    """
    return user.license_type == "PRO"


def demo_days_left(user):
    """
    Visszaadja hány nap van hátra a DEMO verzióból
    """
    if is_pro(user):
        return 999999  # Pro végtelen
    if not user.license_start:
        return DEMO_DAYS
    now = datetime.utcnow()
    delta = now - user.license_start
    remaining = DEMO_DAYS - delta.days
    return max(0, remaining)


def generate_license_key(user_id):
    """
    Egyszerű licensz generátor
    (itt lehet később titkosítani vagy összetettebb logikát)
    """
    now_str = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"PRO-{user_id}-{now_str}"


def validate_license(user, license_key):
    """
    PRO licensz ellenőrzés
    """
    expected = f"PRO-{user.id}-"  # Egyszerű ellenőrzés
    return license_key.startswith(expected)


def license_info_message(user):
    """
    Információ a DEMO/PRO státuszhoz (pl. dashboardon)
    """
    if is_pro(user):
        return f"PRO License Active ✅\nContact: {EMAIL}, {PHONE}, IBAN: {IBAN}"
    else:
        days = demo_days_left(user)
        return f"DEMO License, {days} nap maradt. Upgrade PRO fizetéssel: IBAN {IBAN}, Email {EMAIL}"