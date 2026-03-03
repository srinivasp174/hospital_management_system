from flask import Flask
from config import Config
from extensions import db, jwt, bcrypt, init_redis
import models

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    init_redis(app)
    
    @app.route('/')
    def home():
        return {"message":"HMS Running"}

    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)