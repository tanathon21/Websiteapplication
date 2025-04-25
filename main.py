# Make sure the import path matches your project structure
#main.py
# # This file is part of the Website application.
from Websiteapplication import create_app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)