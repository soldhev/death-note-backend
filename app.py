from flask import Flask
from config import Config
from database import init_db
from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp
from routes.store import store_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db(app)

    app.register_blueprint(store_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
