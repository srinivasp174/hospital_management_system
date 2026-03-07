from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager   
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import redis

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()
cors = CORS()
redis_client = None

def init_redis(app):
    global redis_client
    redis_client = redis.Redis.from_url(app.config["REDIS_URL"])