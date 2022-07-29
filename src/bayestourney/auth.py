from datetime import datetime

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session,
    url_for, current_app, abort
)
from flask_login import (
    login_user, logout_user, login_required, current_user, fresh_login_required
)
from sqlalchemy.exc import NoResultFound
from urllib.parse import urlparse, urljoin

from .models import User
from .database import get_db
from .email import send_email, generate_signed_token, confirm_signed_token

EMAIL_VALIDATION_SALT = "email-validation-salt"
EMAIL_VALIDATION_TIME_LIMIT = 3600 # seconds

bp = Blueprint('auth', __name__, url_prefix='/auth')


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https')
            and ref_url.netloc == test_url.netloc)


def send_confirmation_email(user, token):
    send_email('Please confirm your email address for Tournee',
               sender=current_app.config['ADMIN_MAIL_SENDER'],
               recipients=[user.email],
               text_body=render_template('email/confirm_email.txt',
                                         user=user, token=token),
               html_body=render_template('email/confirm_email.html',
                                         user=user, token=token))


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
            
        if error is None:
            user = User(username, email, password)
            db.add(user)
            db.commit()
            token = generate_signed_token(
                current_app,
                {"name": user.username,
                 "email": user.email
                 },
                EMAIL_VALIDATION_SALT
                )
            send_confirmation_email(user, token)
            current_app.logger.info("Just added new user %s and sent confirmation email",
                                    username)
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/confirm/<token>')
@login_required
def confirm_email(token):
    db = get_db()
    sig_ok, tok_info = confirm_signed_token(
        current_app,
        token,
        EMAIL_VALIDATION_SALT,
        expiration=EMAIL_VALIDATION_TIME_LIMIT
        )
    if sig_ok:
        user = db.query(User).filter_by(email=tok_info["email"]).one()
        if user.confirmed:
            flash('Account already confirmed!  Please login.')
            return redirect(url_for('index'))
        else:
            user.confirmed = True
            user.confirmed_on = datetime.now()
            db.add(user)
            db.commit()
            flash('Thank you for confirming your email!')
            return redirect(url_for('index'))
    else:
        flash('The confirmation link is invalid or has expired.')
        return redirect(url_for('auth.login'))


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember_me = request.form.get('remember_me', 'off')
        db = get_db()
        error = None
        try:
            user = db.query(User).filter_by(email=email).one()
            if user.check_password(password):
                if remember_me == 'on':
                    user.remember_me = True
                else:
                    user.remember_me = False
                db.add(user)
                db.commit()
                login_user(user, remember=user.remember_me)
                current_app.logger.info("Successful login by %s %s, remember = %s",
                                        user.username, user.email, user.remember_me)
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


@bp.route('/change_password', methods=('GET', 'POST'))
@fresh_login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        verify_new_password = request.form['verify_new_password']
        db = get_db()
        user = current_user
        if not user.check_password(old_password):
            error = 'Incorrect current password.'
        elif new_password != verify_new_password:
            error = 'The two copies of the new password do not match.'
        else:
            user.set_password(new_password)
            db.add(user)
            db.commit()
            flash('Your password has been updated!')
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/change_password.html')


@bp.route('/change_email', methods=('GET', 'POST'))
@fresh_login_required
def change_email():
    if request.method == 'POST':
        email_addr = request.form['email']
        current_user.email = email_addr
        current_user.confirmed = False
        current_user.confirmed_on = None
        db = get_db()
        db.add(current_user)
        db.commit()
        token = generate_signed_token(
            current_app,
            {"name": current_user.username,
             "email": current_user.email
             },
            EMAIL_VALIDATION_SALT
        )
        send_confirmation_email(current_user, token)
        current_app.logger.info("Just updated email for user %s to %s and sent confirmation email",
                                current_user.username, current_user.email)
        return redirect(url_for('index'))

    return render_template('auth/change_email.html', user=current_user)
