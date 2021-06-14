"""
This is straight from the tutorial
"""
import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session,
    url_for, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.exc import NoResultFound

from .models import User
from .database import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

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

    return render_template('auth/register.tpl')


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
                session.clear()
                session['user_id'] = user.id
                current_app.logger.info("Successful login by %s",
                                        username)
                return redirect(url_for('index'))
            else:
                error = 'Incorrect password.'
        except NoResultFound:
            error = 'Incorrect username'

        flash(error)

    return render_template('auth/login.tpl')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().query(User).filter_by(id=user_id).one()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

