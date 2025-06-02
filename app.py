import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def create_app():
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    app.secret_key = os.environ.get("SESSION_SECRET", "linkedin-scraper-secret-key")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https
    
    # Configure database
    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        # Render uses postgres:// but SQLAlchemy needs postgresql://
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///linkedin_companies.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Print debug information about environment
    logger.debug(f"DATABASE_URL configured: {app.config['SQLALCHEMY_DATABASE_URI'] is not None}")
    if not database_url:
        logger.warning("No DATABASE_URL found, using SQLite database")
    
    # Initialize database
    db.init_app(app)
    
    # Register routes
    from routes import register_routes
    register_routes(app, db)
    
    # Create tables if they don't exist
    with app.app_context():
        try:
            # Import models to ensure they're registered
            import models  # noqa: F401
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            # Continue running without database - use CSV fallback
    
    return app

# Create the app instance
app = create_app()
