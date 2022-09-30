import pytest
import json
from io import BytesIO
from pprint import pprint
from flask import g, session, url_for
from bayestourney.database import get_db
from .test_endpoints import parse_jqgrid_response_json, parse_ajax_response_json

ENTRANTS_CSV = """name,note
Yorik,
Zander,
"""

BOUTS_CSV = """tourneyName,leftWins,leftPlayerName,rightPlayerName,rightWins,draws,
ignored,2,Yorik,Zander,3,0
ignored,4,Zander,Yorik,1,7
"""

def get_rec_dict(client, endpoint):
    response = client.get(endpoint)
    assert response.status_code == 200
    return parse_jqgrid_response_json(json.loads(response.data.decode('utf-8')))


def get_ajax_rec_dict(client, endpoint):
    response = client.get(endpoint)
    assert response.status_code == 200
    return parse_ajax_response_json(json.loads(response.data.decode('utf-8')))


def test_upload_entrants_no_tourney(auth, client, app):
    auth.login()
    with client:
        before_dict = get_ajax_rec_dict(client, '/ajax/entrants?tourney_id=-1')
        data = {}
        data['file'] = (BytesIO(ENTRANTS_CSV.encode('utf-8')), 'test.csv')
        response =client.post(
            '/upload/entrants', data=data, follow_redirects=True,
            content_type='multipart/form-data'
        )
        assert response.status_code == 200
        after_dict = get_ajax_rec_dict(client, '/ajax/entrants?tourney_id=-1')
    new_recs = [rec for id, rec in after_dict.items() if id not in before_dict]
    new_pairs = [(rec['name'], rec['note']) for rec in new_recs]
    assert len(new_pairs) == 2
    for pair in new_pairs:
        assert pair in [('Yorik', None),
                        ('Zander', None)]
        

def test_upload_entrants_invalid_tourney(auth, client, app):
    auth.login()
    with client:
        before_dict = get_ajax_rec_dict(client, '/ajax/entrants?tourney_id=-1')
        data = {}
        data['file'] = (BytesIO(ENTRANTS_CSV.encode('utf-8')), 'test.csv')
        response =client.post(
            '/upload/entrants?tourney_id=-1', data=data, follow_redirects=True,
            content_type='multipart/form-data'
        )
        assert response.status_code == 400
        

def test_upload_entrants_with_tourney(auth, client, app):
    auth.login()
    with client:
        before_dict = get_ajax_rec_dict(client, '/ajax/entrants?tourney_id=1')
        data = {}
        data['file'] = (BytesIO(ENTRANTS_CSV.encode('utf-8')), 'test.csv')
        response =client.post(
            '/upload/entrants?tourney_id=1', data=data, follow_redirects=True,
            content_type='multipart/form-data'
        )
        assert response.status_code == 200
        after_dict = get_ajax_rec_dict(client, '/ajax/entrants?tourney_id=1')
    new_recs = [rec for id, rec in after_dict.items() if id not in before_dict]
    new_pairs = [(rec['name'], rec['note']) for rec in new_recs]
    assert len(new_pairs) == 2
    for pair in new_pairs:
        assert pair in [('Yorik', None),
                        ('Zander', None)]
        

def test_upload_bouts(auth, client, app):
    auth.login()
    with client:
        before_dict = get_rec_dict(client, '/json/bouts')
        data = {'tourney_id':str(2)}
        data['file'] = (BytesIO(ENTRANTS_CSV.encode('utf-8')), 'test.csv')
        response =client.post(
            '/upload/entrants', data=data, follow_redirects=True,
            content_type='multipart/form-data'
        )
        assert response.status_code == 200
        data['file'] = (BytesIO(BOUTS_CSV.encode('utf-8')), 'test.csv')
        response =client.post(
            '/upload/bouts', data=data, follow_redirects=True,
            content_type='multipart/form-data'
        )
        assert response.status_code == 200
        after_dict = get_rec_dict(client, '/json/bouts')
    new_recs = [rec for id, rec in after_dict.items() if id not in before_dict]
    new_recs = [rec[1:] for rec in new_recs]  # drop the index number
    assert len(new_recs) == 2
    for rec in new_recs:
        assert rec in [[2, 'Yorik', 0, 'Zander', 3, ''],
                       [4, 'Zander', 7, 'Yorik', 1, '']]
