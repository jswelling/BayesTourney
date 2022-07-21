from flask import (
    Blueprint, flash, g, redirect, render_template, request, session,
    url_for, current_app, abort
)
from flask_login import (
    login_user, logout_user, login_required
)
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.exc import NoResultFound
from urllib.parse import urlparse, urljoin

from .models import User
from .database import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https')
            and ref_url.netloc == test_url.netloc)


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif (db.query(User).filter_by(username=username).first()
              is not None):
            error = f"User {username} is already registered."

        if error is None:
            db.add(User(username, generate_password_hash(password)))
            db.commit()
            current_app.logger.info("Just added new user %s",
                                    username)
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        try:
            user = db.query(User).filter_by(username=username).one()
            if check_password_hash(user.password, password):
                login_user(user)
                current_app.logger.info("Successful login by %s",
                                        username)
                next = request.args.get('next')
                if not is_safe_url(next):
                    return abort(400)
                return redirect(next or url_for('index'))
            else:
                error = 'Incorrect password.'
        except NoResultFound:
            error = 'Incorrect username.'

        flash(error)

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))



