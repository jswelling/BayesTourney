import pytest
import json
from io import BytesIO
from pprint import pprint
from flask import g, session, url_for
from bayestourney.database import get_db
from .test_endpoints import _parse_jqgrid_response_json

ENTRANTS_CSV = """name,note
Yorik,
Zander,
"""

BOUTS_CSV = """tourneyName,leftWins,leftPlayerName,rightPlayerName,rightWins,draws,
ignored,2,Yorik,Zander,3,0
ignored,4,Zander,Yorik,1,7
"""

def _get_rec_dict(client, endpoint):
    response = client.get(endpoint)
    assert response.status_code == 200
    return _parse_jqgrid_response_json(json.loads(response.data.decode('utf-8')))


def test_upload_entrants(auth, client, app):
    auth.login()
    with client:
        before_dict = _get_rec_dict(client, '/json/entrants')
        data = {}
        data['file'] = (BytesIO(ENTRANTS_CSV.encode('utf-8')), 'test.csv')
        response =client.post(
            '/upload/entrants', data=data, follow_redirects=True,
            content_type='multipart/form-data'
        )
        assert response.status_code == 200
        after_dict = _get_rec_dict(client, '/json/entrants')
    new_recs = [rec for id, rec in after_dict.items() if id not in before_dict]
    new_recs = [rec[1:] for rec in new_recs]  # drop the index number
    assert len(new_recs) == 2
    for rec in new_recs:
        assert rec in [['Yorik', 0, 0, None],
                       ['Zander', 0, 0, None]]
        

def test_upload_bouts(auth, client, app):
    auth.login()
    with client:
        before_dict = _get_rec_dict(client, '/json/bouts')
        data = {'tournament':str(3)}
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
        after_dict = _get_rec_dict(client, '/json/bouts')
    new_recs = [rec for id, rec in after_dict.items() if id not in before_dict]
    new_recs = [rec[1:] for rec in new_recs]  # drop the index number
    assert len(new_recs) == 2
    for rec in new_recs:
        assert rec in [[2, 'Yorik', 0, 'Zander', 3, ''],
                       [4, 'Zander', 7, 'Yorik', 1, '']]
        
