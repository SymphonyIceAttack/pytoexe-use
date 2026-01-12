from flask import Flask, render_template, request, redirect
from core.license_manager import check_license
from core.payment_gateway import get_payment_info

app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def index():
    if request.method=='POST':
        user = request.form.get('user')
        key = request.form.get('key')
        if check_license(user, key):
            return redirect(f'/dashboard?u={user}')
    return render_template('index.html')

@app.route('/dashboard')
def dash():
    user = request.args.get('u','')
    return render_template('dashboard.html', user=user)

@app.route('/payment')
def pay():
    iban, holder = get_payment_info()
    return render_template('payment.html', iban=iban, holder=holder)

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000)
