from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from utreview import app, db, bcrypt, jwt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_mail import Mail, Message
import random

mail = Mail(app)

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])


@app.route('/api/signup', methods=['POST'])
def register():
    """
    Processes a user's signup and adds them to the database

    Args:
        first_name (string): user first name
        last_name (string): user last name
        email (string): user utexas email
        major (string): user's major
        password (string): user's plaintext password
        profile_pic (string): file name of profile pic

    Returns:
        result (access token): contains securely stored information about the user 
        that can be accessed in the front end
            'first_name' (string): user first name
            'last_name' (string): user last name
            'email' (string): user utexas email
            'major' (string): user's major
            'profile_pic' (string): file name of profile pic
            'verified' (boolean): whether the user has verified their account
        returns error if account already exists for the specified email
    """

    r_val = {'email': None, 'success': 0, 'error': None}

    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    major = request.get_json()['major']
    other_major = request.get_json()['other_major']
    password_hash = bcrypt.generate_password_hash(request.get_json()['password']).decode('utf-8')

    major_id = None
    if(major != None and major != ""):
        dept = Dept.query.filter_by(name=major).first()
        major_id = dept.id

    profile_pics = ProfilePic.query.all()
    profile_pic = random.choice(profile_pics)

    user = User.query.filter_by(email=email).first()
    if user:
        if user.verified:
            r_val['success'] = -1
            r_val['error'] = "An account already exists for this email."
        else:
            r_val['email'] = email
            user.first_name = first_name
            user.last_name = last_name
            user.password_hash = password_hash
            send_confirmation_email(user.email, user.first_name)
    else:
        r_val['email'] = email
        user = User(first_name=first_name, last_name=last_name, 
            email=email, password_hash=password_hash, profile_pic_id=profile_pic.id, 
            verified=False, major_id=major_id, other_major=other_major)
        db.session.add(user)
        # sending confirmation email
        send_confirmation_email(user.email, user.first_name)

    db.session.commit()
    return r_val

@app.route('/api/check_duplicate_email', methods=['POST'])
def check_duplicate_email():
    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()
    error = None
    if user and user.verified:
        error = "An account already exists for this email."
        
    r_val = {'email': email, 'error': error}
    return r_val

@app.route('/api/check_valid_email', methods=['POST'])
def check_valid_email():
    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()
    error = None
    if not user:
        error = "An account does not exist for this email."
        
    r_val = {'email': email, 'error': error}
    return r_val

@app.route('/api/check_verified_email', methods=['POST'])
def check_verified_email():
    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()
    error = None
    if user and not user.verified:
        error = "This account has not been verified."
        
    r_val = {'email': email, 'error': error}
    return r_val

@app.route('/api/check_valid_password', methods=['POST'])
def check_valid_password():
    email = request.get_json()['email']
    password = request.get_json()['password']
    user = User.query.filter_by(email=email).first()

    error = None
    if user and not bcrypt.check_password_hash(user.password_hash, password):
        error = "Invalid email/password combination."

    r_val = {'email': email, 'error': error}
    return r_val


@app.route('/api/send_confirm_email', methods=['POST'])
def send_confirm_email():

    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()

    if user is None:
        return {'success': -3}

    return send_confirmation_email(email, user.first_name)


@app.route('/api/confirm_email', methods=['POST'])
def confirm_email():

    r_val = {'success': 0, 'error': None}

    try:
        token = request.get_json()['token']
        email = s.loads(token, salt='confirm_email', max_age=3600)
        user = User.query.filter_by(email=email).first()

        if user.verified:
            r_val['success'] = -1
            r_val['error'] = "The account has already been verified."
        else:
            user.verified = True
            db.session.commit()
            r_val['success'] = 1
    except SignatureExpired:
        r_val["success"] = -2
        r_val['error'] = "The confirmation code has expired."
    except BadTimeSignature:
        r_val["success"] = -3
        r_val['error'] = "The confirmation code is invalid."
    except KeyError:
        r_val["success"] = -4
        r_val['error'] = "No confirmation code found."

    return r_val


@app.route('/api/login', methods=['POST'])
def login():
    """
    Processes a user's login

    Args:
        email (string): user utexas email
        password (string): user plaintext password

    Returns:
        result (access token): contains securely stored information about the user 
        that can be accessed in the front end
            'first_name' (string): user first name
            'last_name' (string): user last name
            'email' (string): user utexas email
            'major' (string): user's major
            'profile_pic' (string): file name of profile pic
        returns error if invalid username and password combination
    """
    email = request.get_json()['email']
    password = request.get_json()['password']
    r_val = {'token': None, 'success': 0, 'error': None}

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password_hash, password):
        
        if user.verified:
            r_val["success"] = 1
            r_val['token'] = get_user_token(email)
        else:
            r_val["success"] = -101
            r_val['error'] = "The account associated with this email address has not been verified."
            send_confirmation_email(email, user.first_name)
    else:
        if user:
            r_val["success"] = -1
            r_val['error'] = "Invalid email and password combination. Please check your email/password and try again."
        else:
            r_val["success"] = -2
            r_val['error'] = "An account does not exist for this email."

    return r_val


def get_user_token(email):
    
    user = User.query.filter_by(email=email).first()
    access_token = create_access_token(identity={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'major': user.major.name if user.major_id != None else None,
            'profile_pic': user.pic.file_name,
            'other_major': user.other_major
        })
    return access_token


def send_confirmation_email(email, name=None):

    r_val = {'success': 0}

    if name is None:
        
        user = User.query.filter_by(email=email).first()
        if user is None:
            r_val['success'] = -1
            return r_val
        name = user.first_name

    r_val['success'] = 1
    msg = Message(
            'UT Review Confirmation Email',
            sender=("UT Review", "utexas.review@gmail.com"), 
            recipients=[email])

    # TODO: update link as needed
    e_token = s.dumps(email, salt="confirm_email")
    link = "http://localhost:3000/confirm_email?token=" + e_token

    msg.html = render_template('confirm_email.html', name=name, link=link, email=email)
    mail.send(msg)
    return r_val


@app.route('/api/forgot_password', methods=['POST'])
def forgot_password():
    r_val = {'email': None, 'success': 0, 'error': None}

    email = request.get_json()['email']

    user = User.query.filter_by(email=email).first()
    if user == None:
        r_val['success'] = -1
        r_val['error'] = "An account does not exist for this email."
    else:
        r_val['email'] = email
        # sending confirmation email
        send_reset_password(user.email, user.first_name)

    db.session.commit()
    return r_val

def send_reset_password(email, name=None):

    r_val = {'success': 0}

    if name is None:
        
        user = User.query.filter_by(email=email).first()
        if user is None:
            r_val['success'] = -1
            return r_val
        name = user.first_name

    r_val['success'] = 1
    msg = Message(
            'UT Review Password Reset',
            sender=("UT Review", "utexas.review@gmail.com"), 
            recipients=[email])

    # TODO: update link as needed
    e_token = s.dumps(email, salt="reset_password")
    link = "http://localhost:3000/reset_password?token=" + e_token

    msg.html = render_template('reset_password.html', name=name, link=link, email=email)
    mail.send(msg)
    return r_val

@app.route('/api/send_reset_password', methods=['POST'])
def send_reset_email():

    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()

    if user is None:
        return {'success': -3}

    return send_reset_password(email, user.first_name)


@app.route('/api/reset_password_link', methods=['POST'])
def reset_password_link():

    r_val = {'success': 0, 'error': None}

    try:
        token = request.get_json()['token']
        email = s.loads(token, salt='reset_password', max_age=3600)
        user = User.query.filter_by(email=email).first()

        r_val['success'] = 1
    except SignatureExpired:
        r_val["success"] = -2
        r_val['error'] = "The password reset link has expired."
    except BadTimeSignature:
        r_val["success"] = -3
        r_val['error'] = "The password reset link is invalid."
    except KeyError:
        r_val["success"] = -4
        r_val['error'] = "No password reset link found."

    return r_val

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    r_val = {'success': 0, 'error': None}

    email = request.get_json()['email']
    password_hash = bcrypt.generate_password_hash(request.get_json()['password']).decode('utf-8')
    
    user = User.query.filter_by(email=email).first()
    user.password_hash = password_hash
    db.session.commit()

    return r_val