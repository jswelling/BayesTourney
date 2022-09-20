import pytest
import json
from pprint import pprint
from flask import g, session
from bayestourney.database import get_db
from bayestourney.models import DBException

def test_list_select_tourney(client, app, auth):
    auth.login()
    with client:
        rslt = client.get('/list/select_tourney')
    assert rslt.status_code == 200
    expected = """
<select>
<option value=1>test_tourney_1<option>
<option value=2>test_tourney_2<option>
<option value=4>test_tourney_4<option>
<option value=6>test_tourney_6<option>
<option value=7>test_tourney_7<option>
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

def parse_jqgrid_response_json(some_json):
    rec_d = {rec['id']: rec['cell'] for rec in some_json['rows']}
    assert len(rec_d) == some_json['records']
    return rec_d


def parse_ajax_response_json(some_json):
    assert 'status' in some_json
    assert some_json['status'] == 'success'
    assert 'value' in some_json
    rec_d = {rec['id']: rec for rec in some_json['value']}
    return rec_d


def test_edit_tourneys_edit(client, app, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
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
                  'id': 2,
                  'name': 'other new name',
                  'notes': 'other new note'
            })
        assert response.data.decode('utf-8').strip() == '{}'
        after_response = client.get('/json/tourneys')
        assert after_response.status_code == 200
        after_json = json.loads(after_response.data.decode('utf-8'))
    assert before_json['records'] == after_json['records']
    before_rec_d = parse_jqgrid_response_json(before_json)
    after_rec_d = parse_jqgrid_response_json(after_json)
    for (id1, rec1), (id2, rec2) in zip(before_rec_d.items(), after_rec_d.items()):
        if id1 == 1:
            assert int(rec2[0]) == id1
            assert rec2[1] == 'new name'
            assert rec2[2] == rec1[2]
            assert rec2[3] == rec1[3]
            assert rec2[4] == rec1[4]
        elif id1 == 2:
            assert int(rec2[0]) == id1
            assert rec2[1] == 'other new name'
            assert rec2[2] == rec1[2]
            assert rec2[3] == rec1[3]
            assert rec2[4] == 'other new note'
        else:
            assert rec2[0] == rec1[0]
            assert rec2[1] == rec1[1]
            assert rec2[2] == rec1[2]
            assert rec2[3] == rec1[3]
            assert rec2[4] == rec1[4]


def test_edit_tourneys_add(client, app, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
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
    before_rec_d = parse_jqgrid_response_json(before_json)
    after_rec_d = parse_jqgrid_response_json(after_json)
    for id, rec in after_rec_d.items():
        if id in before_rec_d:
            assert rec == before_rec_d[id]
        else:
            assert rec[1] == 'test_tourney_extra'
            assert rec[2] == 'test'
            assert rec[3] == 'test'
            assert rec[4] == 'watch me not fail'


def test_edit_tourneys_del(client, app, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
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
            
    before_rec_d = parse_jqgrid_response_json(before_json)
    before_bouts_rec_d = parse_jqgrid_response_json(before_bouts_json)
    after_rec_d = parse_jqgrid_response_json(after_json)
    after_bouts_rec_d = parse_jqgrid_response_json(after_bouts_json)

    for id, rec in after_rec_d.items():
        assert id != 1
        assert rec == before_rec_d[id]
    for id, rec in after_bouts_rec_d.items():
        assert rec[0] != 'test_tourney_1'
        assert rec == before_bouts_rec_d[id]


def test_edit_entrants_edit(client, app, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
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
    before_rec_d = parse_jqgrid_response_json(before_json)
    after_rec_d = parse_jqgrid_response_json(after_json)
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


def test_edit_entrants_add(client, app, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
        before_response = client.get('/json/entrants')
        assert before_response.status_code == 200
        before_json = json.loads(before_response.data.decode('utf-8'))

        with pytest.raises(DBException) as e:
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
    before_rec_d = parse_jqgrid_response_json(before_json)
    after_rec_d = parse_jqgrid_response_json(after_json)
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
            
    before_rec_d = parse_jqgrid_response_json(before_json)
    after_rec_d = parse_jqgrid_response_json(after_json)
    assert len(after_rec_d) == len(before_rec_d) - 1
    for id, rec in after_rec_d.items():
        assert id != 4
        assert rec == before_rec_d[id]


def test_edit_bouts_edit(client, app, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
        before_response = client.get('/json/bouts')
        assert before_response.status_code == 200
        before_json = json.loads(before_response.data.decode('utf-8'))

        response = client.get('/json/tourneys')
        assert response.status_code == 200
        tourney_d = parse_jqgrid_response_json(
            json.loads(response.data.decode('utf-8'))
            )
            
        response = client.get('/json/entrants')
        assert response.status_code == 200
        entrant_d = parse_jqgrid_response_json(
            json.loads(response.data.decode('utf-8'))
            )

        response = client.post(
            '/edit/bouts',
            data={'oper': 'edit',
                  'id': 1,
                  'tourney': 4
            })
        response = client.post(
            '/edit/bouts',
            data={'oper': 'edit',
                  'id': 2,
                  'rightplayer': 3
            })
        assert response.data.decode('utf-8').strip() == '{}'        
        response = client.post(
            '/edit/bouts',
            data={'oper': 'edit',
                  'id': 3,
                  'leftplayer': 3
            })
        assert response.data.decode('utf-8').strip() == '{}'        
        response = client.post(
            '/edit/bouts',
            data={'oper': 'edit',
                  'id': 4,
                  'notes': 'modified'
            })
        assert response.data.decode('utf-8').strip() == '{}'        
        response = client.post(
            '/edit/bouts',
            data={'oper': 'edit',
                  'id': 3,
                  'rwins': 10,
                  'lwins': 30,
                  'draws': 20
            })
        assert response.data.decode('utf-8').strip() == '{}'        
        after_response = client.get('/json/bouts')
        assert after_response.status_code == 200
        after_json = json.loads(after_response.data.decode('utf-8'))
    assert before_json['records'] == after_json['records']
    before_rec_d = parse_jqgrid_response_json(before_json)
    after_rec_d = parse_jqgrid_response_json(after_json)
    id_set = set([k for k in before_rec_d] + [k for k in after_rec_d])
    for id in id_set:
        assert id in before_rec_d
        assert id in after_rec_d
        rec1 = before_rec_d[id]
        rec2 = after_rec_d[id]
        changed_set = set()
        if id == 1:
            assert rec2[0] == tourney_d[4][1]  # = name of tourney 4
            changed_set.add(0)
        elif id == 2:
            assert rec2[4] == entrant_d[3][1]  # = name of player 3
            changed_set.add(4)
        elif id == 3:
            assert rec2[2] == entrant_d[3][1]  # = name of player 3
            changed_set.add(2)
            assert rec2[1] == 30
            changed_set.add(1)
            assert rec2[3] == 20
            changed_set.add(3)
            assert rec2[5] == 10
            changed_set.add(5)
        elif id == 4:
            assert rec2[6] == 'modified'
            changed_set.add(6)
        for idx, (v1, v2) in enumerate(zip(rec1, rec2)):
            if idx not in changed_set:
                assert v1 == v2, f'mismatch for idx {idx} of id {id}'
        

def test_edit_bouts_add(client, app, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
        before_response = client.get('/json/bouts')
        assert before_response.status_code == 200
        before_json = json.loads(before_response.data.decode('utf-8'))

        response = client.get('/json/tourneys')
        assert response.status_code == 200
        tourney_d = parse_jqgrid_response_json(
            json.loads(response.data.decode('utf-8'))
            )
            
        response = client.get('/json/entrants')
        assert response.status_code == 200
        entrant_d = parse_jqgrid_response_json(
            json.loads(response.data.decode('utf-8'))
            )

        response = client.post(
            '/edit/bouts',
            data={'oper': 'add',
                  'tourney': 2,
                  'leftplayer': 1,
                  'rightplayer': 3,
                  'lwins': 50,
                  'draws': 60,
                  'notes': 'tourney 2 extra bout'
            })
        assert response.status_code == 200
        assert response.data.decode('utf-8').strip() == '{}'        

        after_response = client.get('/json/bouts')
        assert after_response.status_code == 200
        after_json = json.loads(after_response.data.decode('utf-8'))

    assert after_json['records'] == before_json['records'] + 1
    before_rec_d = parse_jqgrid_response_json(before_json)
    after_rec_d = parse_jqgrid_response_json(after_json)
    for id, rec in after_rec_d.items():
        if id in before_rec_d:
            assert rec == before_rec_d[id]
        else:
            assert rec[0] == tourney_d[2][1]
            assert rec[1] == 50
            assert rec[2] == entrant_d[1][1]
            assert rec[3] == 60
            assert rec[4] == entrant_d[3][1]
            assert rec[5] == 0
            assert rec[6] == 'tourney 2 extra bout'


def test_edit_bouts_del(client, app, auth):
    auth.login()
    with client:
        client.get('/') # force current_user to have a value
        before_response = client.get('/json/bouts')
        assert before_response.status_code == 200
        before_json = json.loads(before_response.data.decode('utf-8'))

        with pytest.raises(RuntimeError) as e:
            response = client.post(
                '/edit/bouts',
                data={'oper': 'del',
                      'id': 500
                })
            assert response.status_code == 400

        response = client.post(
            '/edit/bouts',
            data={'oper': 'del',
                  'id': 4
            })
        assert response.status_code == 200
        assert response.data.decode('utf-8').strip() == '{}'        

        after_response = client.get('/json/bouts')
        assert after_response.status_code == 200
        after_json = json.loads(after_response.data.decode('utf-8'))
            
    before_rec_d = parse_jqgrid_response_json(before_json)
    after_rec_d = parse_jqgrid_response_json(after_json)
    assert len(after_rec_d) == len(before_rec_d) - 1
    for id, rec in after_rec_d.items():
        assert id != 4
        assert rec == before_rec_d[id]


def test_ajax_tourneys_settings_get(client, app, auth):
    auth.login()
    with client:
        response = client.get('/ajax/tourneys/settings?tourney_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        values = response_json['value']
        for elt in ['current_user_groups', 'form_name', 'group_name', 'id',
                    'name', 'note', 'owner_name', 'dlg_html']:
            assert elt in values
        assert values['id'] == 1
        assert values['current_user_groups'] == ['test', 'everyone']
        assert '</form>' in values['dlg_html']
        assert values['group_name'] == 'test'
        assert values['name'] == 'test_tourney_1'
        assert values['note'] == 'first test tourney'
        assert values['owner_name'] == 'test'


def test_ajax_tourneys_settings_put(client, app, auth):
    auth.login()
    with client:
        response = client.get('/ajax/tourneys/settings?tourney_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        values = response_json['value']
        data={'tourney_id': '1',
              'group': 'everyone',
              'owner_write': 'false',
              'owner_read': 'false',
              'group_read': 'false',
              }
        put_response = client.put('/ajax/tourneys/settings', data=data)
        put_json = json.loads(put_response.data.decode('utf-8'))
        assert put_json['status'] == 'confirm'
        after_response = client.get('/ajax/tourneys/settings?tourney_id=1')
        after_response_json = json.loads(after_response.data.decode('utf-8'))
        assert after_response_json['status'] == 'success'
        assert 'value' in after_response_json
        after_values = after_response_json['value']
        assert after_values['group_name'] == 'test'
        data['confirm'] = 'true'
        put_response = client.put('/ajax/tourneys/settings', data=data)
        put_json = json.loads(put_response.data.decode('utf-8'))
        assert put_json['status'] == 'success'
        after_response = client.get('/ajax/tourneys/settings?tourney_id=1')
        after_response_json = json.loads(after_response.data.decode('utf-8'))
        assert after_response_json['status'] == 'failure'
        assert 'msg' in after_response_json
        after_msg = after_response_json['msg']
        assert 'does not have read access' in after_msg


def test_ajax_tourneys_settings_put_2(client, app, auth):
    auth.login()
    with client:
        response = client.get('/ajax/tourneys/settings?tourney_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        values = response_json['value']
        data = {'tourney_id': '1',
                'name': 'tourney new name',
                'note': 'and new note'
                }
        put_response = client.put('/ajax/tourneys/settings', data=data)
        put_json = json.loads(put_response.data.decode('utf-8'))
        assert put_json['status'] == 'success'
        after_response = client.get('/ajax/tourneys/settings?tourney_id=1')
        after_response_json = json.loads(after_response.data.decode('utf-8'))
        assert after_response_json['status'] == 'success'
        assert 'value' in after_response_json
        after_values = after_response_json['value']
        assert after_values['name'] == 'tourney new name'
        assert after_values['note'] == 'and new note'


def _htmlify_flags(dct, key_list):
    """
    This simulates checkbox output by replacing dct[key] with 'on' if dct[key]
    is true, and otherwise deleting key from dct.
    """
    for key in key_list:  # simulate what the html map looks like
        if dct[key]:
            dct[key] = 'on'
        else:
            del dct[key]


def test_ajax_tourneys_settings_allflags(client, app, auth):
    auth.login(email='admin@foo.bar', password='AAA') # admin login
    with client:
        response = client.get('/ajax/tourneys/settings?tourney_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        before_values = response_json['value']
        prot_flags = ['owner_read', 'owner_write', 'owner_delete',
                      'group_read', 'group_write', 'group_delete',
                      'other_read', 'other_write', 'other_delete']
        flip_data = {key: not before_values[key] for key in prot_flags}
        flip_data['tourney_id'] = 1
        response = client.put('/ajax/tourneys/settings', data=flip_data)
        response_json = json.loads(response.data.decode('utf-8'))
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        flipped_values = response_json['value']
        for key in prot_flags:
            assert flipped_values[key] == (not before_values[key]), f'{key} does not match'
        response = client.get('/ajax/tourneys/settings?tourney_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        flipped_values = response_json['value']
        for key in prot_flags:
            assert flipped_values[key] == (not before_values[key]), f'{key} does not match'
        flip_flip_data = {key: not flipped_values[key] for key in prot_flags}
        flip_flip_data['tourney_id'] = 1
        response = client.put('/ajax/tourneys/settings', data=flip_flip_data)
        response_json = json.loads(response.data.decode('utf-8'))
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        flip_flipped_values = response_json['value']
        for key in prot_flags:
            assert flip_flipped_values[key] == (not flipped_values[key]), f'{key}'
        response = client.get('/ajax/tourneys/settings?tourney_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        flip_flipped_values = response_json['value']
        for key in prot_flags:
            assert flip_flipped_values[key] == (not flipped_values[key]), f'{key}'


def test_ajax_tourneys_get(client, app, auth):
    auth.login()
    with client:
        response = client.get('/ajax/tourneys?counts=true')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        before_tourneys_dict = {row['id']: row for row in response_json['value']}
        assert 3 not in before_tourneys_dict  # not readable
        assert 5 not in before_tourneys_dict  # ditto
        assert before_tourneys_dict[2] == {'bouts': 1,
                                           'entrants': 2,
                                           'id': 2,
                                           'name': 'test_tourney_2',
                                           'note': 'second test tourney'}


def test_ajax_tourneys_put(client, app, auth):
    auth.login()
    with client:
        response = client.get('/ajax/tourneys?counts=true')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        before_tourneys_dict = {row['id']: row for row in response_json['value']}
        response = client.put('/ajax/tourneys',
                              data={'action':'create',
                                    'name':'test_tourney_1',
                                    'note':'that name was not unique'
                                    }
                              )
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'failure'
        assert 'msg' in response_json
        assert 'test_tourney_1' in response_json['msg']
        assert 'already exists' in response_json['msg']
        response = client.put('/ajax/tourneys',
                              data={'action':'create',
                                    'name':'some unique name',
                                    'note':'that name was unique'
                                    }
                              )
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        response = client.get('/ajax/tourneys?counts=true')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        after_create_dict = {row['id']: row for row in response_json['value']}
        new_keys = [key for key in after_create_dict if key not in before_tourneys_dict]
        assert len(new_keys) == 1
        new_key = new_keys[0]
        response = client.put('/ajax/tourneys',
                              data={'action':'delete',
                                    'tourney_id':new_key
                                    }
                              )
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        response = client.get('/ajax/tourneys?counts=true')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        after_delete_dict = {row['id']: row for row in response_json['value']}
        assert new_key not in after_delete_dict


def test_ajax_entrants_get(client, app, auth):
    auth.login()
    with client:
        response = client.get('/ajax/entrants?tourney_id=3')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'failure'
        assert 'msg' in response_json
        assert 'does not have read access' in response_json['msg']
        response = client.get('/ajax/entrants?tourney_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        player_id_set = set(elt['id'] for elt in response_json['value'])
        assert player_id_set == set([1, 2, 3])


def test_ajax_entrants_put(client, app, auth):
    auth.login()
    with client:
        response = client.get('/ajax/entrants?tourney_id=4')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        response = client.put('/ajax/entrants',
                              data={'tourney_id': 4,
                                    'action': 'add',
                                    'player_id': 1
                                    }
                              )
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'failure'
        assert 'msg' in response_json
        assert 'does not have write access' in response_json['msg']
        response = client.get('/ajax/entrants?tourney_id=1')
        before_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in before_json
        assert before_json['status'] == 'success'
        before_set = set(elt['id'] for elt in before_json['value'])
        response = client.put('/ajax/entrants',
                              data={'tourney_id': 1,
                                    'action': 'add',
                                    'player_id': 4
                                    }
                              )
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        response = client.get('/ajax/entrants?tourney_id=1')
        after_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in after_json
        assert after_json['status'] == 'success'
        after_set = set(elt['id'] for elt in after_json['value'])
        assert len(after_json['value']) == len(before_json['value']) + 1
        assert after_set ^ before_set == set([4])
        response = client.put('/ajax/entrants',
                              data={'tourney_id': 1,
                                    'action': 'delete',
                                    'player_id': 4
                                    }
                              )
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        response = client.get('/ajax/entrants?tourney_id=1')
        after_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in after_json
        assert after_json['status'] == 'success'
        after_set = set(elt['id'] for elt in after_json['value'])
        assert after_set == before_set
        response = client.put('/ajax/entrants',
                              data={'tourney_id': 1,
                                    'action': 'create',
                                    'name': 'Some New Guy',
                                    'note': 'Creating player on the fly'
                                    }
                              )
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        response = client.get('/ajax/entrants?tourney_id=1')
        after_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in after_json
        assert after_json['status'] == 'success'
        after_set = set(elt['id'] for elt in after_json['value'])
        change_set = after_set - before_set
        assert len(change_set) == 1
        new_player_id = list(change_set)[0]
        response = client.get('/ajax/entrants?tourney_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        row_dict = {row['id']: row for row in response_json['value']}
        new_row = row_dict[new_player_id]
        assert new_row['name'] == 'Some New Guy'
        assert new_row['note'] == 'Creating player on the fly'


def test_ajax_entrants_settings_get(client, app, auth):
    auth.login()
    with client:
        response = client.get('/ajax/entrants/settings?player_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        values = response_json['value']
        assert values.get('id', 0) == 1
        assert values.get('name', '') == 'Andy'
        assert values.get('note', '') == 'test player 1'


def test_ajax_entrants_settings_put(client, app, auth):
    auth.login()
    with client:
        response = client.get('/ajax/entrants/settings?player_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert response_json.get('status', '') == 'success'
        before_values = response_json.get('value', {})
        for elt in ['id', 'name', 'note']:
            assert elt in before_values
        for key in ['name', 'note']:
            response = client.put('/ajax/entrants/settings',
                                  data = {'player_id': 1,
                                          key: f'changed {key}'
                                          }
                                  )
            response_json = json.loads(response.data.decode('utf-8'))
            assert response_json.get('status', '') == 'success'
            response = client.get('/ajax/entrants/settings?player_id=1')
            response_json = json.loads(response.data.decode('utf-8'))
            values = response_json.get('value', {})
            new_val = values.get(key, '')
            assert new_val == f'changed {key}'
