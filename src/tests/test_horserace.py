import pytest
import json
from pprint import pprint
from flask import g, session
from bayestourney.database import get_db


def test_horserace_go(auth, client, app):
    auth.login()
    with client:
        response = client.post(
            '/horserace_go',
            json={
                'tourney': 1,
                'checkboxes': {'1': True,
                               '2': True,
                               '3': False}
            },
            headers={'content-type':'application/json'}
        )
        assert response.status_code == 200
        response_json = json.loads(response.data.decode('utf-8').strip())
        assert 'announce_html' in response_json
        assert 'Betty' in response_json['announce_html']
        assert 'image' in response_json
        assert 'svg' in response_json['image']
