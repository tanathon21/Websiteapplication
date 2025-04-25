from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from os import path
import os
from datetime import datetime

# Initialize SQLAlchemy with no settings
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
DB_NAME = 'database.db'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize db with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    app.jinja_env.globals.update(enumerate=enumerate)
    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from .views import views
    from .auth import auth
    app.register_blueprint(views)
    app.register_blueprint(auth)

    # Import models
    from .models import User, Role

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create tables and default data
    with app.app_context():
        db.create_all()

        roles = ['NoPosition', 'Employee', 'Manager', 'Admin']
        for role_name in roles:
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name))

        from werkzeug.security import generate_password_hash
        if not User.query.filter_by(username='admin').first():
            admin_role = Role.query.filter_by(name='Admin').first()
            admin_user = User(
                first_name='Admin',
                last_name='User',
                email='admin@example.com',
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role_id=admin_role.id if admin_role else None
            )
            db.session.add(admin_user)
        db.session.commit()

    # Template filter
    def get_user_name(user_id):
        user = User.query.get(user_id)
        if user:
            return f"{user.first_name} {user.last_name}"
        return "Unknown User"
    app.add_template_filter(get_user_name, 'get_user_name')

    # Context processor
    @app.context_processor
    def inject_now():
        return {'now': datetime.now}

    # Template filter for current datetime
    def template_now():
        return datetime.now()
    app.add_template_filter(template_now, 'now')
    
    @app.template_global()
    def get_user_name(user_id):
        """Helper function to get a user's full name by their ID"""
        user = User.query.get(user_id)
        if user:
            return f"{user.first_name} {user.last_name}"
        return "Unknown User"
    return app
