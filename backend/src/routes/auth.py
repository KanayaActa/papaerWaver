from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import db, User, Paper, Comment, Bookmark, Vote
import requests
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Username, email, and password are required'}), 400
    
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        affiliation=data.get('affiliation', ''),
        field_of_study=data.get('field_of_study', '')
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully', 'user': user.to_dict()}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        return jsonify({'message': 'Login successful', 'user': user.to_dict()}), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@auth_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@auth_bp.route('/profile/<int:user_id>', methods=['PUT'])
def update_profile(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if data.get('affiliation'):
        user.affiliation = data['affiliation']
    if data.get('field_of_study'):
        user.field_of_study = data['field_of_study']
    
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully', 'user': user.to_dict()})

