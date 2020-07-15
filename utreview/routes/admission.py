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
    password_hash = bcrypt.generate_password_hash(request.get_json()['password']).decode('utf-8')
    dept = Dept.query.filter_by(name=major).first()

    profile_pics = ProfilePic.query.all()
    profile_pic = random.choice(profile_pics)

    user = User.query.filter_by(email=email).first()
    if user:
        if user.verified:
            r_val['success'] = -1
            r_val['error'] = "An account already exists for this email."
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.password_hash = password_hash
    else:
        r_val['email'] = user.email
        user = User(first_name=first_name, last_name=last_name, 
            email=email, password_hash=password_hash, profile_pic_id=profile_pic.id, 
            verified=False, major_id=dept.id)
        db.session.add(user)
        # sending confirmation email
        send_confirm_email(user.email, user.first_name)

    db.session.commit()
    return r_val


@app.route('/api/send_confirm_email', methods=['POST'])
def send_confirm_email():

    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()

    if user is None:
        return {'success': -3}

    return send_confirm_email(email, user.first_name)


@app.route('/api/confirm_email', methods=['POST'])
def confirm_email():

    r_val = {'token': None, 'success': 0, 'error': None}

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
            r_val['token'] = get_user_token(email)
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
            r_val['error'] = "Account not verified."
    else:
        r_val["success"] = -1
        r_val['error'] = "Invalid username and password combination."

    return r_val


def get_user_token(email):
    
    user = User.query.filter_by(email=email).first()
    access_token = create_access_token(identity={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'major': user.major.name,
            'profile_pic': user.pic
        })
    return access_token


def send_confirm_email(email, name=None):

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

