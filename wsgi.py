import os
import sys
import logging
from app import app, db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path, exist_ok=True)
    logger.info(f"Instance path: {app.instance_path}")
except Exception as e:
    logger.error(f"Failed to create instance directory: {e}")
    raise

# Initialize the database
try:
    with app.app_context():
        db.create_all()
        logger.info("Database tables created (if they don't exist)")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting application on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
