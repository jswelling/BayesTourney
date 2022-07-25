from flask import (
    Blueprint, flash, g, redirect, render_template, request, session,
    url_for, current_app, abort
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)
from sqlalchemy.exc import NoResultFound
from urllib.parse import urlparse, urljoin

from .models import User
from .database import get_db
from .email import send_email

bp = Blueprint('auth', __name__, url_prefix='/auth')

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https')
            and ref_url.netloc == test_url.netloc)


def send_congrats_email(user):
    send_email('[Congrats] You are registered',
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user),
               html_body=render_template('email/reset_password.html',
                                         user=user))


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if current_user.is_authenticated:
        return redirect(urlfor('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        verify_password = request.form['verify_password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not email:
            error = 'Email is required.'
        elif not verify_password:
            error = 'Verify Password is required.'
        elif verify_password != password:
            error = 'Passwords do not match.'
        
        elif (db.query(User).filter_by(email=email).first()
              is not None):
            error = f"There is already a user registered for {email} ."

        elif (db.query(User).filter_by(username=username).first()
              is not None):
            error = f"The username {username} is already in use."
        print(f'ERROR is <{error}>')
            
        if error is None:
            user = User(username, email, password)
            db.add(user)
            db.commit()
            #send_congrats_email(user)
            current_app.logger.info("Just added new user %s",
                                    username)
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        try:
            user = db.query(User).filter_by(email=email).one()
            if user.check_password(password):
                login_user(user)
                current_app.logger.info("Successful login by %s %s",
                                        user.username, user.email)
                next = request.args.get('next')
                if not is_safe_url(next):
                    return abort(400)
                return redirect(next or url_for('index'))
            else:
                error = 'Incorrect password.'
        except NoResultFound:
            error = 'No known user has that email address.'

        flash(error)

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))



