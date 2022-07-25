import pytest
from flask import session
from flask_login import current_user
from bayestourney.database import get_db
from bayestourney.models import User

def test_register(client, app):
    assert client.get('/auth/register').status_code == 200
    response = client.post(
        '/auth/register', data={'username': 'a',
                                'email': 'a',
                                'verify_password': 'a',
                                'password': 'a'}
    )
    assert 'http://localhost/auth/login' == response.headers['Location']

    with app.app_context():
        assert get_db().execute(
            "SELECT * FROM user WHERE username = 'a'",
        ).fetchone() is not None


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
    assert response.headers['Location'] == 'http://localhost/'

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
    print(f'HERE {response.data}')
    assert message in response.data

def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert 'user_id' not in session
