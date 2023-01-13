from flask import Flask, g
from flask.sessions import SecureCookieSessionInterface
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

class CustomSessionInterface(SecureCookieSessionInterface):
    """Disable default cookie generation."""
    def should_set_cookie(self, *args, **kwargs):
        if g.get('login_via_request'):
            print("Custom session login via header")
            return False
        return True

    # """Prevent creating session from API requests."""
    # def save_session(self, *args, **kwargs):
    #     if g.get('login_via_request'):
    #         print("Custom session login via header")
    #         return
    #     return super(CustomSessionInterface, self).save_session(*args,
    #                                                             **kwargs)

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'secret-key-goes-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    

    db.init_app(app)
    login_manager.init_app(app)
    # app.session_interface = CustomSessionInterface()

    with app.app_context():
        from . import auth
        from . import main
        from . import api
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(main.main_bp)
        app.register_blueprint(api.api_bp)

        app.session_interface = CustomSessionInterface()
        
        db.create_all()

        return app