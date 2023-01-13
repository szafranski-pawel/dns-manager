from http import HTTPStatus
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for, g
from flask_login import current_user, login_user, user_loaded_from_request

from . import login_manager
from .forms import LoginForm, SignupForm
from .models import User, db

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
    # Validate login attempt
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
        existing_user = db.session.execute(db.select(User).filter_by(email=form.email.data)).first()
        if existing_user is None:
            user = User(
                name=form.name.data,
                email=form.email.data,
                domain=form.domain.data
            )
            user.set_password(form.password.data)
            user.generate_api_key()
            db.session.add(user)
            db.session.commit()  # Create new user
            login_user(user)  # Log in as newly created user
            return redirect(url_for('main_bp.dashboard'))
        flash('A user already exists with that email address.')
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
        user = db.session.execute(db.select(User).filter_by(master_api_key=api_key)).first()
        if user is not None:
            return db.session.get(User, user.User.id)
        else:
            return None
    return None

@login_manager.unauthorized_handler
def unauthorized():
    if request.blueprint == 'api_bp':
        abort(HTTPStatus.UNAUTHORIZED)
    flash('You must be logged in to view that page.')
    return redirect(url_for('auth_bp.login'))

@user_loaded_from_request.connect
def load_user_from_request(self, user=None):
    g.login_via_request = True
