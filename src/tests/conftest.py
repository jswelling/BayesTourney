import os
from pathlib import Path
import tempfile
import re

from flask_login import FlaskLoginClient

from sqlalchemy.sql import text
import pytest
from bayestourney import create_app
from bayestourney.database import get_db, init_db
from bayestourney.models import User

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app({
        'TESTING': True,
        'LOGIN_DISABLED': True,
        'DATABASE': db_path,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{db_path}",
        'SECRET_KEY': '1234',
        'TEMPLATE_FOLDER': 'views',
        'UPLOAD_FOLDER': '/tmp',
        'SESSION_SCRATCH_DIR': '/tmp',
        'ADMIN_MAIL_SENDER': 'someadmin',
        'SERVER_NAME': 'fake.name.for.testing.org',
    })
    app.test_client_class = FlaskLoginClient

    with app.app_context():
        init_db()

        with open(Path(__file__).parent / 'data.sql') as file:
            statements = re.split(r';\s*$', file.read(), flags=re.MULTILINE)
            for statement in statements:
                if statement:
                    get_db().execute(text(statement))
            get_db().commit()

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()

class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, email='foo@bar.baz', password='test'):
        return self._client.post(
            '/auth/login',
            data={'email': email, 'password': password}
        )

    def logout(self):
        return self._client.get('/auth/logout')


@pytest.fixture
def auth(client):
    return AuthActions(client)
