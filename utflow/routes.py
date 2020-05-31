from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utflow.models import User, Dept, Prof
from utflow import app, db, bcrypt, jwt


@app.route('/api/signup', methods=['POST'])
def register():
    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    major = request.get_json()['major']
    password = bcrypt.generate_password_hash(
        request.get_json()['password']).decode('utf-8')

    user = User.query.filter_by(email=email).first()
    if user:
        result = jsonify({"error": "An account already exists for this email"})
    else:
        user = User(first_name=first_name, last_name=last_name,
                    email=email, major=major, password=password)
        db.session.add(user)
        db.session.commit()

        result_user = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password,
            'major': major
        }
        result = jsonify({'result': result_user})

    return result


@app.route('/api/login', methods=['POST'])
def login():
    email = request.get_json()['email']
    password = request.get_json()['password']

    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity = {
            'first_name': user.first_name, 
            'last_name': user.last_name,
            'email': user.email,
            'major': user.major
            })
        result = access_token
    else:
        result = jsonify({"error": "Invalid username and password"})

    return result


@app.route('/api/get-course-num', methods=['GET'])
def getCourseNum():
    result = None
    return result


@app.route('/api/get-prof-name', methods=['GET'])
def getCourseNum():
    result = Prof.query()
    return result