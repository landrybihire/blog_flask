from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_ckeditor import CKEditor
from flask_bootstrap5 import Bootstrap # Import Flask-Bootstrap5
from config import Config
import os
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
ckeditor = CKEditor()
bootstrap = Bootstrap() # Initialize Flask-Bootstrap5

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    ckeditor.init_app(app)
    bootstrap.init_app(app) # Initialize Bootstrap5
    
    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.blog import bp as blog_bp
    app.register_blueprint(blog_bp, url_prefix='/blog')
    
    # Create upload folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow}

    return app

from app import models
