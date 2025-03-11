from flask import Flask
from .main import main as main_blueprint

def create_app():
    app = Flask(__name__)
    
    # Configuration settings can be added here
    app.config.from_object('config.Config')

    # Register Blueprints here
    app.register_blueprint(main_blueprint)

    return app