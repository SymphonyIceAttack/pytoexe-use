from flask import Flask, render_template
from modules.IT_Asset_Manager import demo as IT_demo, pro as IT_pro
from modules.AI_Document_Analyzer import demo as AI_demo, pro as AI_pro
from modules.License_Server import license_api

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')  # Dashboard linkekkel

@app.route('/IT/demo')
def it_demo():
    return IT_demo.run_demo()

@app.route('/IT/pro')
def it_pro():
    if license_api.validate_license(user_id='Istvan'):
        return IT_pro.run_pro()
    else:
        return "Pro version locked. Please purchase license."

@app.route('/AI/demo')
def ai_demo():
    return AI_demo.run_demo()

@app.route('/AI/pro')
def ai_pro():
    if license_api.validate_license(user_id='Istvan'):
        return AI_pro.run_pro()
    else:
        return "Pro version locked. Please purchase license."

if __name__ == "__main__":
    app.run()