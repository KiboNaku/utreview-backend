
from flask import render_template
from utreview import app


"""routes used in backend to visualize files such as the confirmation email"""


@app.route("/")
@app.route("/confirm_email")
def home():
    return render_template('confirm_email.html', name='Andy', link='https://www.google.com')

@app.route("/confirm_email_referral")
def referral():
    return render_template('confirm_email_referral.html', name='Andy', link='https://www.google.com')

@app.route("/reset_password")
def password():
    return render_template('reset_password.html', name='Andy', link='https://www.google.com')

@app.route("/create_password")
def create_password():
    return render_template('create_password.html', name='Andy', link='https://www.google.com')
