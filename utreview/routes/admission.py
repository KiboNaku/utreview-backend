"""
This file contains routes to register, login, and deal with user's needs:
    register,
    login,
    forgot_password,
    create_password,
    confirm_email,
    refresh_user_token
"""

from flask import render_template, request
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from utreview import app, db, bcrypt, jwt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_mail import Mail, Message
from smtplib import SMTPRecipientsRefused
import random
from utreview.services.logger import logger

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

    # initialize return value
    r_val = {'email': None, 'success': 0, 'error': None}

    # get args from front end
    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    major = request.get_json()['major']
    other_major = request.get_json()['other_major']

    # get password hash depending on whether password was sent
    if(request.get_json()['password'] != None): 
        password_hash = bcrypt.generate_password_hash(
            request.get_json()['password']).decode('utf-8')
    else: 
        password_hash = None

    # determine user major (none or other)
    major_id = None
    if(major != None and major != ""):
        dept = Dept.query.filter_by(name=major).first()
        major_id = dept.id

    # choose random profile pic for the user
    profile_pics = ProfilePic.query.all()
    profile_pic = random.choice(profile_pics)

    # check if user account has already been taken
    user = User.query.filter_by(email=email).first()
    if user:
        if user.verified:
            r_val['success'] = -1
            r_val['error'] = "An account already exists for this email."
        else:
            r_val['email'] = email

            # send confirmation email
            try:
                send_confirmation_email(user.email, first_name)
                user.first_name = first_name
                user.last_name = last_name
                user.password_hash = password_hash
            except SMTPRecipientsRefused as e:
                logger.error(f"Confirmation email error: {e}")
                r_val['success'] = -2
                r_val['error'] = "Invalid email.\nPlease make sure your entry does not include @utexas.edu as that is included automatically."
    else:
        # make new unverified user instance and add to database
        r_val['email'] = email
        user = User(first_name=first_name, last_name=last_name,
                    email=email, password_hash=password_hash, profile_pic_id=profile_pic.id,
                    verified=False, major_id=major_id, other_major=other_major)
        db.session.add(user)

        # send confirmation email
        try:
            send_confirmation_email(user.email, first_name)
        except SMTPRecipientsRefused as e:
            logger.error(f"Confirmation email error: {e}")
            r_val['success'] = -2
            r_val['error'] = "Invalid email.\nPlease make sure your entry does not include @utexas.edu as that is included automatically."

    db.session.commit()

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
    # get args from front end
    email = request.get_json()['email']
    password = request.get_json()['password']

    # initialize return value
    r_val = {'token': None, 'success': 0, 'error': None}
    user = User.query.filter_by(email=email).first()

    # if no password, then its a login with google
    if password == None:
        # check if user is in the system
        if user:
            # check if the user is verified
            if user.verified:
                r_val["success"] = 1
                r_val['token'] = get_user_token(email)
            else:
                # send confirmation email
                try:
                    r_val["success"] = -101
                    r_val['error'] = "The account associated with this email address has not been verified."
                    send_confirmation_email(email, user.first_name)
                except SMTPRecipientsRefused as e:
                    logger.error(f"Confirmation email error: {e}")
                    r_val['success'] = -3
                    r_val['error'] = "Invalid email.\nPlease make sure your entry does not include @utexas.edu as that is included automatically."
        else:
            r_val["success"] = -2
            r_val['error'] = "An account does not exist for this email."
    else:
        # check if the email/password combination is valid
        if user and bcrypt.check_password_hash(user.password_hash, password):
            # check if the user is verified
            if user.verified:
                r_val["success"] = 1
                r_val['token'] = get_user_token(email)
            else:
                # send confirmation email
                try:
                    r_val["success"] = -101
                    r_val['error'] = "The account associated with this email address has not been verified."
                    send_confirmation_email(email, user.first_name)
                except SMTPRecipientsRefused as e:
                    logger.error(f"Confirmation email error: {e}")
                    r_val['success'] = -2
                    r_val['error'] = "Invalid email.\nPlease make sure your entry does not include @utexas.edu as that is included automatically."
        else:
            # either account doesn't exist, or it's the wrong password
            if user:
                r_val["success"] = -1
                r_val['error'] = "Invalid email and password combination. Please check your email/password and try again."
            else:
                r_val["success"] = -2
                r_val['error'] = "An account does not exist for this email."

    return r_val

@app.route('/api/check_duplicate_email', methods=['POST'])
def check_duplicate_email():
    """
    Checks if an account already exists for the given email
    Args:
        email (string): email entered by the user

    Returns:
        r_val (object): contains the error, if any, and the email
    """

    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()
    error = None

    if user and user.verified:
        error = "An account already exists for this email."

    r_val = {'email': email, 'error': error}

    return r_val


@app.route('/api/check_valid_email', methods=['POST'])
def check_valid_email():
    """
    Checks if the account is a valid email in the system
    Args:
        email (string): email entered by the user

    Returns:
        r_val (object): contains the error, if any, and the email
    """
    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()
    error = None

    if not user:
        error = "An account does not exist for this email."

    r_val = {'email': email, 'error': error}

    return r_val


@app.route('/api/check_verified_email', methods=['POST'])
def check_verified_email():
    """
    Checks if the account has been verified for the given email
    Args:
        email (string): email entered by the user

    Returns:
        r_val (object): contains the error, if any, and the email
    """
    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()
    error = None

    if user and not user.verified:
        error = "This account has not been verified."

    r_val = {'email': email, 'error': error}

    return r_val

@app.route('/api/check_email_password', methods=['POST'])
def check_email_password():
    """
    Checks if the account associated with the email has a password
    Args:
        email (string): email entered by the user

    Returns:
        r_val (object): contains the error, if any, and the email
    """
    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()
    error = None

    if user and not user.password_hash:
        error = "This account does not have an associated password. Login with Google and then create a password."

    r_val = {'email': email, 'error': error}

    return r_val


@app.route('/api/check_valid_password', methods=['POST'])
def check_valid_password():
    """
    Checks if an email/password combination is valid
    Args:
        email (string): email entered by the user
        password (string): password entered by the user

    Returns:
        r_val (object): contains the error, if any, and the email
    """
    email = request.get_json()['email']
    password = request.get_json()['password']
    user = User.query.filter_by(email=email).first()

    error = None
    if user and user.password_hash:
        if not bcrypt.check_password_hash(user.password_hash, password):
            error = "Invalid email/password combination."

    r_val = {'email': email, 'error': error}

    return r_val


@app.route('/api/send_confirm_email', methods=['POST'])
def send_confirm_email():
    """
    Sends a confirmation email to the user email address
    Args:
        email (string): email entered by the user

    """

    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()

    if user is None:
        return {'success': -3}

    return send_confirmation_email(email, user.first_name)


@app.route('/api/confirm_email', methods=['POST'])
def confirm_email():
    """
    Checks if the confirmation link is valid
    Args:
        token (string): token obtained from the confirmation link

    Returns:
        r_val (object): contains the error, if any
    """

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
    except AttributeError:
        r_val["success"] = -5
        r_val['error'] = "The email cannot be found."

    return r_val

@app.route('/api/refresh_user_token', methods=['POST'])
def refresh_user_token():
    """
    Generates a new user access token for a given user email
    Args:
        email (string): email entered by the user

    Returns:
        token (object): contains the user access token
    """
    email = request.get_json()['email']

    return {'token': get_user_token(email) }

def get_user_token(email):
    """
    Checks if an account already exists for the given email
    Args:
        email (string): email entered by the user

    Returns:
        access_token (object):
            access_token = create_access_token(identity={
                'first_name' (string): user first name,
                'last_name' (string): user last name,
                'email' (string): user email,
                'major' (string): user major (if chosen from default list),
                'profile_pic' (string): user profile pic file name,
                'other_major' (string): user other major
            }) 
    """

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
    """
    Generates a custom confirmation email and sends to user email address
    Args:
        email (string): email entered by the user
        name (string): user's first name

    """

    r_val = {'success': 0}

    # obtain user first name
    if name is None:

        user = User.query.filter_by(email=email).first()
        if user is None:
            r_val['success'] = -1
            return r_val
        name = user.first_name

    # generate email to send to user
    r_val['success'] = 1
    msg = Message(
        'UT Review Confirmation Email',
        sender=("UT Review", "utexas.review@gmail.com"),
        recipients=[email])

    # generate confirm email token
    e_token = s.dumps(email, salt="confirm_email")
    website = 'https://utexasreview.com/'
    # website = 'http://localhost:3000/'

    link = website + "confirm-email?token=" + e_token

    # send confirmation email
    msg.html = render_template(
        'confirm_email_referral.html', name=name, link=link, email=email)
    mail.send(msg)

    return r_val


@app.route('/api/forgot_password', methods=['POST'])
def forgot_password():
    """
    Sends a reset password email to the user email address
    Args:
        email (string): email entered by the user
    
    Returns:
        r_val (object): Returns an error, if any, and the email

    """
    # get args and initialize return value
    r_val = {'email': None, 'success': 0, 'error': None}
    email = request.get_json()['email']

    # check if user account exists
    user = User.query.filter_by(email=email).first()
    if user == None:
        r_val['success'] = -1
        r_val['error'] = "An account does not exist for this email."
    else:
        r_val['email'] = email
        # send reset password email
        send_reset_password(user.email, user.first_name)

    db.session.commit()

    return r_val

@app.route('/api/send_create_password', methods=['POST'])
def send_create_email():
    """
    Sends a create password email to the user email address
    Args:
        email (string): email entered by the user

    """

    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()

    if user is None:
        return {'success': -3}

    return send_create_password(email, user.first_name)

def send_create_password(email, name=None):
    """
    Generates a create password email and sends it to the user email address
    Args:
        email (string): email entered by the user
        name (string): user's first name

    """

    r_val = {'success': 0}

    # obtain user's first name
    if name is None:

        user = User.query.filter_by(email=email).first()
        if user is None:
            r_val['success'] = -1
            return r_val
        name = user.first_name

    # generate email to send to user
    r_val['success'] = 1
    msg = Message(
        'UT Review Password Creation',
        sender=("UT Review", "utexas.review@gmail.com"),
        recipients=[email])

    # generate create password token
    e_token = s.dumps(email, salt="create_password") 
    website = 'https://utexasreview.com/'
    # website = 'http://localhost:3000/'
    link = website + "create-password?token=" + e_token

    # send create password email
    msg.html = render_template('create_password.html', name=name, link=link)
    mail.send(msg)

    return r_val

@app.route('/api/create_password_link', methods=['POST'])
def create_password_link():
    """
    Checks if the create password link is valid
    Args:
        token (string): create password link token
    
    Returns:
        r_val (object): returns an error, if any

    """

    r_val = {'success': 0, 'error': None}

    try:
        token = request.get_json()['token']
        email = s.loads(token, salt='create_password', max_age=3600)
        user = User.query.filter_by(email=email).first()

        r_val['success'] = 1
    except SignatureExpired:
        r_val["success"] = -2
        r_val['error'] = "The password creation link has expired."
    except BadTimeSignature:
        r_val["success"] = -3
        r_val['error'] = "The password creation link is invalid."
    except KeyError:
        r_val["success"] = -4
        r_val['error'] = "No password creation link found."

    return r_val

def send_reset_password(email, name=None):
    """
    Generates a reset password email and sends it to the user email address
    Args:
        email (string): email entered by the user
        name (string): user's first name

    """

    r_val = {'success': 0}

    # obtain user's first name
    if name is None:

        user = User.query.filter_by(email=email).first()
        if user is None:
            r_val['success'] = -1
            return r_val
        name = user.first_name

    # generate email to send to user
    r_val['success'] = 1
    msg = Message(
        'UT Review Password Reset',
        sender=("UT Review", "utexas.review@gmail.com"),
        recipients=[email])

    # generate reset password token
    e_token = s.dumps(email, salt="reset_password") 
    website = 'https://utexasreview.com/'
    # website = 'http://localhost:3000/'
    link = website + "reset-password?token=" + e_token

    # send reset password email
    msg.html = render_template('reset_password.html', name=name, link=link)
    mail.send(msg)

    return r_val

@app.route('/api/send_reset_password', methods=['POST'])
def send_reset_email():
    """
    Sends a reset password email to the user email address
    Args:
        email (string): email entered by the user

    """

    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()

    if user is None:
        return {'success': -3}

    return send_reset_password(email, user.first_name)

@app.route('/api/reset_password_link', methods=['POST'])
def reset_password_link():
    """
    Checks if a reset password link is valid
    Args:
        token (string): reset password link token

    """

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
    """
    Resets a user password and generates a new password hash
    Args:
        email (string): email entered by the user
        password (string): password entered by the user

    """
    r_val = {'success': 0, 'error': None}


    # get args from front end and generate new password hash
    email = request.get_json()['email']
    password_hash = bcrypt.generate_password_hash(
        request.get_json()['password']).decode('utf-8')

    # replace password hash
    user = User.query.filter_by(email=email).first()
    user.password_hash = password_hash
    db.session.commit()

    return r_val
