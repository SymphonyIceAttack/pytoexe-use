import json

LICENSES = {
    "Istvan": {"status": "active", "iban": "LT81 3250 0757 5026 3901", "email": "istvanmajsai70@gmail.com"}
}

def validate_license(user_id):
    user = LICENSES.get(user_id)
    if user and user['status'] == 'active':
        return True
    return False

def generate_license(user_id):
    # Automatikusan létrehoz fizetés után
    LICENSES[user_id] = {"status": "active"}
    return LICENSES[user_id]