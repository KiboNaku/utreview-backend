from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utflow.models import *
from utflow import app, db, bcrypt, jwt

@app.route('/api/signup', methods=['POST'])
def register():
    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    major = request.get_json()['major']
    password = bcrypt.generate_password_hash(
        request.get_json()['password']).decode('utf-8')
    dept = Dept.query.filter_by(name=major).first()
    

    user = User.query.filter_by(email=email).first()
    if user:
        result = jsonify({"error": "An account already exists for this email"})
    else:
        user = User(first_name=first_name, last_name=last_name, 
        email=email, password=password, major_id=dept.id)
        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(identity={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'major': dept.name,
            'image_file': 'corgi1.jpg'
        })
        result = access_token

    return result


@app.route('/api/login', methods=['POST'])
def login():
    email = request.get_json()['email']
    password = request.get_json()['password']

    user = User.query.filter_by(email=email).first()

    # print(user, bcrypt.check_password_hash(user.password, password), password, user.password)
    
    if user and bcrypt.check_password_hash(user.password, password):
        major = Dept.query.filter_by(id=user.major_id).first()
        access_token = create_access_token(identity={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'major': major.name,
            'profile_pic': 'corgi1.jpg'
        })
        result = access_token
    else:
        result = jsonify({"error": "Invalid username and password"})

    return result