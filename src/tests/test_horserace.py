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
        before_response = client.get('/json/horserace?tourney=1')
        assert before_response.status_code == 200
        before_json = json.loads(before_response.data.decode('utf-8'))
        before_rec_d = parse_jqgrid_response_json(before_json)
        ckbox_get_response = client.get('/ajax/horserace/checkbox?tourney_id=1&player_id=3')
        assert ckbox_get_response.status_code == 200
        ckbox_get_json = json.loads(ckbox_get_response.data.decode('utf-8'))
        assert ckbox_get_json['value'] == 'true'
        assert before_rec_d[3][6] == '3+'
        ckbox_put_response = client.put('/ajax/horserace/checkbox?tourney_id=1&player_id=3&state=false')
        assert ckbox_put_response.status_code == 200
        ckbox_put_json = json.loads(ckbox_put_response.data.decode('utf-8'))
        assert ckbox_put_json['value'] == 'false'
        after_response = client.get('/json/horserace?tourney=1')
        assert after_response.status_code == 200
        after_json = json.loads(after_response.data.decode('utf-8'))
        after_rec_d = parse_jqgrid_response_json(after_json)
        assert after_rec_d[3][6] == '3-'
        
        


