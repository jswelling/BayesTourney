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
<option value=4>Donna<option>
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


def _parse_jqgrid_response_json(some_json):
    rec_d = {rec['id']: rec['cell'] for rec in some_json['rows']}
    assert len(rec_d) == some_json['records']
    return rec_d


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
    before_rec_d = _parse_jqgrid_response_json(before_json)
    after_rec_d = _parse_jqgrid_response_json(after_json)
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


def test_edit_tourneys_add(client, app):
    with client:
        before_response = client.get('/json/tourneys')
        assert before_response.status_code == 200
        before_json = json.loads(before_response.data.decode('utf-8'))

        with pytest.raises(RuntimeError) as e:
            response = client.post(
                '/edit/tourneys',
                data={'oper': 'add',
                      'name': 'test_tourney_2',
                      'notes': 'watch me fail'
                })
            assert response.status_code == 400

        response = client.post(
            '/edit/tourneys',
            data={'oper': 'add',
                  'name': 'test_tourney_extra',
                  'notes': 'watch me not fail'
            })
        assert response.status_code == 200
        assert response.data.decode('utf-8').strip() == '{}'        

        after_response = client.get('/json/tourneys')
        assert after_response.status_code == 200
        after_json = json.loads(after_response.data.decode('utf-8'))

    assert after_json['records'] == before_json['records'] + 1
    before_rec_d = _parse_jqgrid_response_json(before_json)
    after_rec_d = _parse_jqgrid_response_json(after_json)
    for id, rec in after_rec_d.items():
        if id in before_rec_d:
            assert rec == before_rec_d[id]
        else:
            assert rec[1] == 'test_tourney_extra'
            assert rec[2] == 'watch me not fail'


def test_edit_tourneys_del(client, app):
    with client:
        before_response = client.get('/json/tourneys')
        assert before_response.status_code == 200
        before_json = json.loads(before_response.data.decode('utf-8'))
        before_bouts_response = client.get('/json/bouts')
        assert before_bouts_response.status_code == 200
        before_bouts_json = json.loads(before_bouts_response.data.decode('utf-8'))

        response = client.post(
            '/edit/tourneys',
            data={'oper': 'del',
                  'id': 1
            })
        assert response.status_code == 200
        assert response.data.decode('utf-8').strip() == '{}'        

        after_response = client.get('/json/tourneys')
        assert after_response.status_code == 200
        after_json = json.loads(after_response.data.decode('utf-8'))
        after_bouts_response = client.get('/json/bouts')
        assert after_bouts_response.status_code == 200
        after_bouts_json = json.loads(after_bouts_response.data.decode('utf-8'))
            
    before_rec_d = _parse_jqgrid_response_json(before_json)
    before_bouts_rec_d = _parse_jqgrid_response_json(before_bouts_json)
    after_rec_d = _parse_jqgrid_response_json(after_json)
    after_bouts_rec_d = _parse_jqgrid_response_json(after_bouts_json)

    for id, rec in after_rec_d.items():
        assert id != 1
        assert rec == before_rec_d[id]
    for id, rec in after_bouts_rec_d.items():
        assert rec[0] != 'test_tourney_1'
        assert rec == before_bouts_rec_d[id]


def test_edit_entrants_edit(client, app):
    with client:
        before_response = client.get('/json/entrants')
        assert before_response.status_code == 200
        before_json = json.loads(before_response.data.decode('utf-8'))

        response = client.post(
            '/edit/entrants',
            data={'oper': 'edit',
                  'id': 1,
                  'name': 'new name'
            })
        assert response.data.decode('utf-8').strip() == '{}'        
        response = client.post(
            '/edit/entrants',
            data={'oper': 'edit',
                  'id': 2,
                  'notes': 'new note'
            })
        assert response.data.decode('utf-8').strip() == '{}'        
        response = client.post(
            '/edit/entrants',
            data={'oper': 'edit',
                  'id': 3,
                  'name': 'other new name',
                  'notes': 'other new note'
            })
        assert response.data.decode('utf-8').strip() == '{}'
        after_response = client.get('/json/entrants')
        assert after_response.status_code == 200
        after_json = json.loads(after_response.data.decode('utf-8'))
    assert before_json['records'] == after_json['records']
    before_rec_d = _parse_jqgrid_response_json(before_json)
    after_rec_d = _parse_jqgrid_response_json(after_json)
    id_set = set([k for k in before_rec_d] + [k for k in after_rec_d])
    for id in id_set:
        assert id in before_rec_d
        assert id in after_rec_d
        rec1 = before_rec_d[id]
        rec2 = after_rec_d[id]
        assert int(rec1[0]) == int(rec2[0])  # id
        assert int(rec1[2]) == int(rec2[2])  # num_bouts
        assert int(rec1[3]) == int(rec2[3])  # num_tournies
        if id == 1:
            assert rec2[1] == 'new name'
            assert rec2[4] == rec1[4]
        elif id == 2:
            assert rec2[1] == rec1[1]
            assert rec2[4] == 'new note'
        elif id == 3:
            assert rec2[1] == 'other new name'
            assert rec2[4] == 'other new note'
        else:
            assert rec2[1] == rec1[1]
            assert rec2[4] == rec1[4]


def test_edit_entrants_add(client, app):
    with client:
        before_response = client.get('/json/entrants')
        assert before_response.status_code == 200
        before_json = json.loads(before_response.data.decode('utf-8'))

        with pytest.raises(RuntimeError) as e:
            response = client.post(
                '/edit/entrants',
                data={'oper': 'add',
                      'name': 'Andy',
                      'notes': 'watch me fail'
                })
            assert response.status_code == 400

        response = client.post(
            '/edit/entrants',
            data={'oper': 'add',
                  'name': 'Walter',
                  'notes': 'watch me not fail'
            })
        assert response.status_code == 200
        assert response.data.decode('utf-8').strip() == '{}'        

        after_response = client.get('/json/entrants')
        assert after_response.status_code == 200
        after_json = json.loads(after_response.data.decode('utf-8'))

    assert after_json['records'] == before_json['records'] + 1
    before_rec_d = _parse_jqgrid_response_json(before_json)
    after_rec_d = _parse_jqgrid_response_json(after_json)
    for id, rec in after_rec_d.items():
        if id in before_rec_d:
            assert rec == before_rec_d[id]
        else:
            assert rec[1] == 'Walter'
            assert rec[4] == 'watch me not fail'


def test_edit_entrants_del(client, app):
    with client:
        before_response = client.get('/json/entrants')
        assert before_response.status_code == 200
        before_json = json.loads(before_response.data.decode('utf-8'))

        response = client.post(
            '/edit/entrants',
            data={'oper': 'del',
                  'id': 1
            })
        assert response.status_code == 200
        reply_json = json.loads(response.data.decode('utf-8'))
        assert reply_json['status'] == 'failure'

        response = client.post(
            '/edit/entrants',
            data={'oper': 'del',
                  'id': 4
            })
        assert response.status_code == 200
        reply_json = json.loads(response.data.decode('utf-8'))
        assert reply_json['status'] == 'success'

        after_response = client.get('/json/entrants')
        assert after_response.status_code == 200
        after_json = json.loads(after_response.data.decode('utf-8'))
            
    before_rec_d = _parse_jqgrid_response_json(before_json)
    after_rec_d = _parse_jqgrid_response_json(after_json)
    assert len(after_rec_d) == len(before_rec_d) - 1
    for id, rec in after_rec_d.items():
        assert id != 4
        assert rec == before_rec_d[id]
