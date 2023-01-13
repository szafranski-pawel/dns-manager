from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required, logout_user

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Logged-in User Dashboard."""
    return render_template(
        'dashboard.jinja2',
        title='Dashboard.',
        template='dashboard-template',
        current_user=current_user,
        body="You are now logged in!"
    )

@main_bp.route("/logout")
@login_required
def logout():
    """User log-out logic."""
    logout_user()
    return redirect(url_for('auth_bp.login'))