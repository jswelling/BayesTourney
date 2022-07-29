import pytest
import json
from pprint import pprint
from flask import g, session, render_template
from bayestourney.database import get_db
from bayestourney.email import send_email, generate_signed_token, confirm_signed_token

TESTING_SALT = 'salt for testing'


def test_send_email(auth, client, app):
    auth.login()
    with app.app_context():
        send_email("Hello World",
                   sender="test_sender@nowhere.org",
                   recipients=["test_recipients@elsewhere.org"],
                   text_body=render_template('email/confirm_email.txt',
                                             user={'username':'someguy'},
                                             token='thisisatoken'),
                   html_body=render_template('email/confirm_email.html',
                                             user={'username':'someguy'},
                                             token='thisisatoken')
                   )


def test_signing(app):
    payload = {'foo': 'bar', 'baz': [1, 2, 4]}
    token = generate_signed_token(app, payload, TESTING_SALT)
    sig_okay, parsed_payload = confirm_signed_token(app, token, TESTING_SALT)
    assert sig_okay
    assert parsed_payload == payload


def test_signing_2(app):
    payload = {'foo': 'bar', 'baz': [1, 2, 4]}
    token = generate_signed_token(app, payload, TESTING_SALT)
    sig_okay, parsed_payload = confirm_signed_token(app, token, TESTING_SALT[1:])
    assert not sig_okay

