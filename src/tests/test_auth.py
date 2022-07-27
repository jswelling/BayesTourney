import pytest
from datetime import datetime, timedelta
from flask import session
from flask_login import current_user
from flask_mail import Mail
from bayestourney.database import get_db
from bayestourney.models import User
from bayestourney.email import generate_signed_token
from bayestourney.auth import EMAIL_VALIDATION_SALT

def test_register(client, app):
    assert client.get('/auth/register').status_code == 200
    mail = Mail(app)
    with mail.record_messages() as outbox:
        response = client.post(
            '/auth/register', data={'username': 'a',
                                    'email': 'a',
                                    'verify_password': 'a',
                                    'password': 'a'}
        )
        assert 'http://fake.name.for.testing.org/auth/login' == response.headers['Location']

        with app.app_context():
            assert get_db().execute(
                "SELECT * FROM user WHERE username = 'a'",
            ).fetchone() is not None
    assert len(outbox) == 1
    assert outbox[0].subject == 'Please confirm your email address for Tournee'


@pytest.mark.parametrize(('username', 'email', 'password', 'verify_password', 'message'), (
    ('', '', '', '', b'Username is required.'),
    ('a', 'foo@bar.com', '', '', b'Password is required.'),
    ('a', 'foo@bar.com', 'abc', 'bcd', b'Passwords do not match.'),
    ('someone', 'foo@bar.baz', 'abc', 'abc', b'already a user registered for'),
    ('test', 'foo@bar.blrfl', 'abc', 'abc', b'already in use'),
))
def test_register_validate_input(client, username, email, password, verify_password, message):
    response = client.post(
        '/auth/register',
        data={'username': username, 'password': password,
              'email': email, 'verify_password': verify_password}
    )
    assert message in response.data

def test_login(app, client, auth):
    assert client.get('/auth/login').status_code == 200
    response = auth.login()
    assert response.headers['Location'] == 'http://fake.name.for.testing.org/'

    with client:
        client.get('/')
        assert session['_user_id'] == '1'
        assert getattr(current_user, 'username') == 'test'


@pytest.mark.parametrize(('email', 'password', 'message'), (
    ('a@b.com', 'test', b'No known user has that email address.'),
    ('foo@bar.baz', 'a', b'Incorrect password.'),
))
def test_login_validate_input(client, email, password, message):
    response = client.post(
        '/auth/login',
        data={'email': email, 'password': password}
    )
    assert message in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert 'user_id' not in session


def test_confirm(client, auth, app):
    auth.login()
    with client:
        salt = EMAIL_VALIDATION_SALT
        client.get('/')  # forces current_user to have a value
        db = get_db()
        user = db.query(User).filter_by(email=current_user.email).one()
        user.confirmed = False
        db.add(user)
        db.commit()
        user = db.query(User).filter_by(email=current_user.email).one()
        assert not user.confirmed
        token = generate_signed_token(app,
                                      {
                                          'name': current_user.username,
                                          'email': current_user.email,
                                       },
                                      salt)
        resp = client.get('/auth/confirm/' + token)
        user = db.query(User).filter_by(email=current_user.email).one()
        assert user.confirmed
        assert user.confirmed_on - datetime.now() < timedelta(seconds=5)
