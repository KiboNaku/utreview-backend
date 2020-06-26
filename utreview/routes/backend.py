
from flask import render_template


"""routes used in backend to visualize files such as the confirmation email"""


@app.route("/")
@app.route("/confirm_email")
def home():
    return render_template('confirm_email.html', name='Andy', link='https://www.google.com')
