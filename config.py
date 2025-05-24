import os
from dotenv import load_dotenv

# Only load .env file if we're in development
if os.environ.get('FLASK_ENV') != 'production':
    load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Storage configuration
    STORAGE_URL = os.environ.get('STORAGE_URL', 'file://' + os.path.join(BASE_DIR, 'static', 'uploads'))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')  # Kept for backwards compatibility
    
    # S3 Configuration (optional)
    S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
    S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
    S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL')
    S3_PUBLIC_URL = os.environ.get('S3_PUBLIC_URL')

    @staticmethod
    def init_app(app):
        # Create necessary directories
        os.makedirs(os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')), exist_ok=True)
        
        # Only create upload folder if using local storage
        if app.config['STORAGE_URL'].startswith('file://'):
            storage_path = app.config['STORAGE_URL'].replace('file://', '')
            os.makedirs(storage_path, exist_ok=True)
