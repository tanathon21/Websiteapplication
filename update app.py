# Add this import at the top of your app.py
from context_processors import register_context_processors

# Add this line after creating the Flask app
register_context_processors(app)