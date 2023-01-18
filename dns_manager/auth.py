from functools import wraps
import os
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for, g
from flask_login import current_user, login_user, user_loaded_from_request

from . import login_manager
from .forms import LoginForm, SignupForm
from .models import User, db, UserNode, Admin

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Log-in page for registered users.
    GET requests serve Log-in page.
    POST requests validate and redirect user to dashboard.
    """
    # Bypass if user is logged in
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(password=form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main_bp.dashboard'))
        flash('Invalid username/password combination')
        return redirect(url_for('auth_bp.login'))
    return render_template(
        'login.jinja2',
        form=form,
        title='Log in.',
        template='login-page'
    )

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    User sign-up page.
    GET requests serve sign-up page.
    POST requests validate form & user creation.
    """
    form = SignupForm()
    if form.validate_on_submit():
        if '.' in form.domain.data:
            flash('Domain name cannot have any dots.')
        existing_user = db.session.execute(db.select(User).filter_by(email=form.email.data)).first()
        existing_domain = db.session.execute(db.select(User).filter_by(domain=form.domain.data)).first()
        if existing_user is None and existing_domain is None:
            user = User(
                name=form.name.data,
                email=form.email.data,
                domain=form.domain.data
            )
            user.set_password(form.password.data)
            user.generate_api_key()
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('main_bp.dashboard'))
        elif existing_user is not None:
            flash('A user already exists with that email address.')
        elif existing_user is None and existing_domain is not None:
            flash('This subdomain is already in use.')
    return render_template(
        'signup.jinja2',
        title='Create an Account.',
        form=form,
        template='signup-page'
    )

@login_manager.user_loader
def load_user(user_id):
    """Check if user is logged-in upon page load."""
    if user_id is not None:
        return db.session.get(User, user_id)
    return None

@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.headers.get('X-Api-Key')
    if api_key:
        user = User.query.filter_by(api_key=api_key).first()
        iot_node = UserNode.query.filter_by(api_key=api_key).first()
        if user is not None:
            current_app.logger.info('logged in successfully')
            return db.session.get(User, user.id)
        elif iot_node is not None:
            current_app.logger.info('logged in successfully')
            return db.session.get(UserNode, iot_node.id)
        elif api_key == os.environ['ADMIN_API_KEY']:
            return Admin()
        else:
            return None
    return None

@login_manager.unauthorized_handler
def unauthorized():
    if request.blueprint in ['api_bp', 'dns_bp']:
        return "", 401
    flash('You must be logged in to view that page.')
    return redirect(url_for('auth_bp.login'))

@user_loaded_from_request.connect
def load_user_from_request(self, user=None):
    g.login_via_request = True

def roles_required(*role_names):
    def decorator_roles_required(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if current_app.config.get("LOGIN_DISABLED"):
                pass
            elif not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            elif not current_user.has_roles(role_names):
                return current_app.login_manager.unauthorized()
            # flask 1.x compatibility
            # current_app.ensure_sync is only available in Flask >= 2.0
            if callable(getattr(current_app, "ensure_sync", None)):
                return current_app.ensure_sync(func)(*args, **kwargs)
            return func(*args, **kwargs)
        return decorated_view
    return decorator_roles_required