#context_processors.py
# #context_processors.py
from datetime import datetime
from flask import current_app
from Websiteapplication.models import User

def add_template_functions():
    """Add custom functions to Jinja templates"""
    def get_user_name(user_id):
        """Get user's name from ID"""
        user = User.query.get(user_id)
        if user:
            return f"{user.first_name} {user.last_name}"
        return "Unknown User"
    
    def now():
        """Return current datetime"""
        return datetime.now()
    
    return dict(
        get_user_name=get_user_name,
        now=now
    )

def register_context_processors(app):
    app.context_processor(add_template_functions)