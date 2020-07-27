from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from utreview import app, db, bcrypt, jwt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_mail import Mail, Message
import random

mail = Mail(app)

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])


@app.route('/api/contact_us_message', methods=['POST'])
def contact_us_message():

    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    message = request.get_json()['message']

    msg = Message(
        'User Feedback',
        sender=("UT Review", "utexas.review@gmail.com"),
        recipients=("UT Review", "utexas.review@gmail.com"))

    msg.html = render_template(
        'confirm_email.html', name=name, link=link, email=email)
    mail.send(msg)

    return r_val
