from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from flask_login import login_user, logout_user, current_user, login_required
from . import db
from .models import User, Role

auth = Blueprint('auth', __name__)

# Custom role-required decorator
def role_required(role_names):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role.name not in role_names:
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('views.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        thai_first_name = request.form.get('thai_first_name')
        thai_last_name = request.form.get('thai_last_name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('auth.register'))
        
        # Get NoPosition role
        noposition_role = Role.query.filter_by(name='NoPosition').first()
        
        # Create new user
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            thai_first_name=thai_first_name,
            thai_last_name=thai_last_name,
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            role_id=noposition_role.id
        )
        
        # Add to database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Use Flask-Login's login_user instead of session
            login_user(user)
            flash(f'Welcome back, {user.first_name}!', 'success')
            
            # Redirect based on role
            if user.role.name == 'Admin':
                return redirect(url_for('views.admin_page'))
            elif user.role.name == 'Manager':
                return redirect(url_for('views.manager_page'))
            elif user.role.name == 'Employee':
                return redirect(url_for('views.employee_page'))
            else:  # NoPosition
                return redirect(url_for('views.noposition_page'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))