from flask import Flask
from config import Config
from extensions import db, jwt, bcrypt, cors, init_redis
import models
from create_admin import create_admin
from routes.admin_routes import admin_bp
from routes.auth_routes import auth_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app)
    init_redis(app)
    
    @app.route('/')
    def home():
        return {"message":"HMS Running"}

    with app.app_context():
        db.create_all()
        create_admin()
        
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    
    return app

app = create_app()


if __name__ == "__main__":
    app.run(debug=True)