import logging
import os
from dotenv import load_dotenv
from datetime import timedelta

DEBUG = False
load_dotenv()
logging.basicConfig(filename="error.log", level=logging.DEBUG,
                    format=f"%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s")
logging.getLogger('flask_cors').level = logging.DEBUG

def get_id_list():
    id_list_str = os.environ.get('EVENT_IDS', '')
    return [int(id) for id in id_list_str.split(',') if id]

SECRET_KEY = os.environ.get("SECRET_KEY")
SQLALCHEMY_TRACK_MODIFICATIONS = False
SESSION_TYPE = "filesystem"
if os.environ.get("DEBUG_ENV") == "dev":
    DEBUG = True
DEBUG = True
CORS_METHODS = ["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"]
CORS_HEADERS = ["Content-Type", "Authorization", "Access-Control-Allow-Credentials"]
CORS_SUPPORTS_CREDENTIALS = True
CORS_ORIGINS = ["*"]
DATABASE_USER = os.environ.get('DATABASE_USER')
DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')
DATABASE_HOST = os.environ.get('DATABASE_HOST')
DATABASE = os.environ.get('DATABASE')
# SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL")
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,  # Maximum number of connections in the pool
    "pool_recycle": 300,  # Maximum time (in seconds) between connection recycling
    "pool_pre_ping": True,  # Test if connections are alive before using them
}
CACHE_TYPE = 'simple'
CACHE_DEFAULT_TIMEOUT = 300 
CACHE_THRESHOLD = 1000 
JWT_SECRET_KEY = ''
EVENT_IDS = get_id_list()
JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = 25
MAIL_USERNAME = os.getenv("EMAIL")
MAIL_DEFAULT_SENDER = os.getenv("EMAIL")
MAIL_PASSWORD = os.getenv("MAIL_PASS")
SECURITY_EMAIL_SENDER = os.getenv("EMAIL")
MAIL_USE_TLS = True
MAIL_USE_SSL = False