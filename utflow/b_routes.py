from flask import render_template, url_for, flash, redirect
from utflow import app
from utflow.models import *
from utflow.forms import RegistrationForm, LoginForm, DeptForm


@app.route("/")
@app.route("/home")
def home():
    # form = DeptForm()
    # depts = Dept.query.all()
    return render_template('confirm_email.html', name='Andy', link='https://www.google.com')


@app.route("/register", methods=['GET', 'POST'])
def b_register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def b_login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == 'admin@blog.com' and form.password.data == 'password':
            flash('You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)
