import pytest
import json
from pprint import pprint
from flask import g, session
from bayestourney.database import get_db
from .test_endpoints import parse_jqgrid_response_json


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


def test_horserace_get_bouts_graph(auth, client, app):
    auth.login()
    with client:
        response = client.post(
            '/horserace_get_bouts_graph',
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
        assert 'Bouts for' in response_json['announce_html']
        assert 'image' in response_json
        assert 'svg' in response_json['image']
        assert 'Andy' in response_json['image']
        assert 'Betty' in response_json['image']


def test_horserace_table(auth, client, app):
    auth.login()
    with client:
        tbl_response = client.get('/json/horserace?tourney=1')
        assert tbl_response.status_code == 200
        tbl_json = json.loads(tbl_response.data.decode('utf-8'))
        rec_d = parse_jqgrid_response_json(tbl_json)
        with open('/tmp/debug.txt','w') as f:
            from pprint import pprint
            pprint(tbl_json, stream=f)
            pprint(rec_d, stream=f)
