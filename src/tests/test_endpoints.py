import pytest
import json
from flask import g, session
from bayestourney.database import get_db

def test_list_select_tourney(client, app):
    with client:
        rslt = client.get('/list/select_tourney')
    assert rslt.status_code == 200
    expected = """
<select>
<option value=1>test_tourney_1<option>
<option value=2>test_tourney_2<option>
<option value=3>test_tourney_3<option>
<option value=4>test_tourney_4<option>
<option value=5>test_tourney_5<option>
</select>
"""
    assert rslt.data.decode('utf-8').strip() == expected.strip()

def test_list_select_entrant(client, app):
    with client:
        rslt = client.get('/list/select_entrant')
    assert rslt.status_code == 200
    expected = """
<select>
<option value=1>Andy<option>
<option value=2>Betty<option>
<option value=3>Cal<option>
</select>
"""
    assert rslt.data.decode('utf-8').strip() == expected.strip()

#
# To add later-
# - upload/entrants
# - upload/bouts
# - download/bouts
# - download/entrants
#

def test_edit_tourneys_edit(client, app):
    with client:
        before_response = client.get('/json/tourneys')
        assert before_response.status_code == 200
        before_json = json.loads(before_response.data.decode('utf-8'))

        response = client.post(
            '/edit/tourneys',
            data={'oper': 'edit',
                  'id': 1,
                  'name': 'new name'
            })
        assert response.data.decode('utf-8').strip() == '{}'        
        response = client.post(
            '/edit/tourneys',
            data={'oper': 'edit',
                  'id': 2,
                  'notes': 'new note'
            })
        assert response.data.decode('utf-8').strip() == '{}'        
        response = client.post(
            '/edit/tourneys',
            data={'oper': 'edit',
                  'id': 3,
                  'name': 'other new name',
                  'notes': 'other new note'
            })
        assert response.data.decode('utf-8').strip() == '{}'
        after_response = client.get('/json/tourneys')
        assert after_response.status_code == 200
        after_json = json.loads(after_response.data.decode('utf-8'))
    assert before_json['records'] == after_json['records']
    before_rec_d = {rec['id']: rec['cell'] for rec in before_json['rows']}
    after_rec_d = {rec['id']: rec['cell'] for rec in after_json['rows']}
    for (id1, rec1), (id2, rec2) in zip(before_rec_d.items(), after_rec_d.items()):
        assert id1 == id2
        if id1 == 1:
            assert int(rec2[0]) == id1
            assert rec2[1] == 'new name'
            assert rec2[2] == rec1[2]
        elif id1 == 2:
            assert int(rec2[0]) == id1
            assert rec2[1] == rec1[1]
            assert rec2[2] == 'new note'
        elif id1 == 3:
            assert int(rec2[0]) == id1
            assert rec2[1] == 'other new name'
            assert rec2[2] == 'other new note'
        else:
            assert rec2[1] == rec1[1]
            assert rec2[0] == rec1[0]
            assert rec2[2] == rec1[2]
