import pytest
import json
from pprint import pprint
from flask import g, session
from bayestourney.database import get_db
from bayestourney.models import DBException
from bayestourney.settings_constants import SETTINGS_GROUPS, ALLOWED_SETTINGS

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
<option value=5>Eli<option>
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

        response = client.post(
            '/edit/entrants',
            data={'oper': 'add',
                  'name': 'Andy',
                  'notes': 'watch me fail'
                  })
        assert response.status_code == 403

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
        for key, val in [('owner_name', 'test'),
                         ('group_name', 'test'),
                         ('name', 'test_tourney_1'),
                         ('note', 'first test tourney'),
                         ('owner_name', 'test'),
                         ('owner_delete', True),
                         ('owner_read', True),
                         ('owner_write', True),
                         ('group_read', True),
                         ('group_write', False),
                         ('group_delete', False),
                         ('other_read', False),
                         ('other_write', False),
                         ('other_delete', False),
                         ('bp_draws_rule', 'bp_draws_1_pts'),
                         ('bp_losses_rule', 'bp_losses_1_pts'),
                         ('bp_wins_rule', 'bp_wins_2_pts'),
                         ('hr_draws_rule', 'hr_draws_rule_ignore'),
                         ]:
            assert values[key] == val


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


def test_ajax_tourneys_settings_put_3(client, app, auth):
    auth.login()
    with client:
        values = _get_values_for_tourney(client, tourney_id=1)
        no_change_data = {'tourney_id': '1'}
        for setting_name in SETTINGS_GROUPS['tourney_group']:
            assert setting_name in values
            assert values[setting_name] in ALLOWED_SETTINGS[setting_name]
            no_change_data[setting_name] = values[setting_name]
        put_response = client.put('/ajax/tourneys/settings', data=no_change_data)
        put_json = json.loads(put_response.data.decode('utf-8'))
        assert 'status' in put_json
        assert put_json['status'] == 'success'
        assert _get_values_for_tourney(client, tourney_id=1) == values
        for setting_name in SETTINGS_GROUPS['tourney_group']:
            targets = [name for name in ALLOWED_SETTINGS[setting_name]
                       if values[setting_name] != name]
            targets.append(values[setting_name])
            for target in targets:
                data = {'tourney_id': '1',
                        setting_name: target}
                put_response = client.put('/ajax/tourneys/settings', data=data)
                put_json = json.loads(put_response.data.decode('utf-8'))
                assert 'status' in put_json
                assert put_json['status'] == 'success'
                values = _get_values_for_tourney(client, tourney_id=1)
                assert setting_name in values
                assert values[setting_name] == target


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


def test_ajax_bouts_get(client, app, auth):
    auth.login()
    with client:
        response = client.get('/ajax/bouts?tourney_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        assert len(response_json['value']) == 3
        found_it = False
        for rec in response_json['value']:
            if rec['lplayer'] == 'Andy' and rec['rplayer'] == 'Betty':
                check_dct = {
                    'draws': 2,
                    'lplayer': 'Andy',
                    'lplayer_id': 1,
                    'lwins': 3,
                    'note': 'tourney 1 set 1',
                    'rplayer': 'Betty',
                    'rplayer_id': 2,
                    'rwins': 5,
                    'tourney_id': 1
                }
                for key, val in check_dct.items():
                    assert key in rec
                    assert rec[key] == val
                found_it = True
                break
        assert found_it


def test_ajax_bouts_get_all(client, app, auth):
    auth.login()
    with client:
        response = client.get('/ajax/bouts?tourney_id=-1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        assert len(response_json['value']) == 4
        found_it = False
        for rec in response_json['value']:
            if rec['lplayer'] == 'Andy' and rec['rplayer'] == 'Betty':
                check_dct = {
                    'draws': 2,
                    'lplayer': 'Andy',
                    'lplayer_id': 1,
                    'lwins': 3,
                    'note': 'tourney 1 set 1',
                    'rplayer': 'Betty',
                    'rplayer_id': 2,
                    'rwins': 5,
                    'tourney_id': 1
                }
                for key, val in check_dct.items():
                    assert key in rec
                    assert rec[key] == val
                found_it = True
                break
        assert found_it
        found_it = False
        for rec in response_json['value']:
            if rec['tourney_id'] != 1:
                found_it = True
                break
        assert found_it


def test_ajax_bouts_put(client, app, auth):
    auth.login()
    with client:
        response = client.get('/ajax/bouts?tourney_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        assert len(response_json['value']) == 3
        before_rec_dct = {rec['id']: rec for rec in response_json['value']}
        response = client.put('/ajax/bouts',
                              data={
                                  'action': 'add',
                                  'tourney_id': 1,
                                  'lplayer': 3,
                                  'rplayer': 1,
                                  'lwins': 1,
                                  'draws': 2,
                                  'rwins': 3,
                                  'note': 'Andy vs Cal'
                              })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        response = client.get('/ajax/bouts?tourney_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        assert len(response_json['value']) == 4
        after_rec_dct = {rec['id']: rec for rec in response_json['value']}
        extra_id = (set(after_rec_dct.keys()) - set(before_rec_dct.keys())).pop()
        extra_rec = after_rec_dct[extra_id]
        assert extra_rec == {'draws': 2,
                             'id': extra_id,
                             'lplayer': 'Cal',
                             'lplayer_id': 3,
                             'lwins': 1,
                             'note': 'Andy vs Cal',
                             'rplayer': 'Andy',
                             'rplayer_id': 1,
                             'rwins': 3,
                             'tourney_id': 1}
        response = client.put('/ajax/bouts',
                              data={
                                  'action': 'delete',
                                  'tourney_id': 1,
                                  'bout_id': extra_id
                              })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        response = client.get('/ajax/bouts?tourney_id=1')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        assert len(response_json['value']) == 3
        after_rec_dct = {rec['id']: rec for rec in response_json['value']}
        assert after_rec_dct == before_rec_dct
        response = client.put('/ajax/bouts',
                              data={
                                  'action': 'add',
                                  'tourney_id': 1,
                                  'lplayer': 5,
                                  'rplayer': 1,
                                  'lwins': 1,
                                  'draws': 2,
                                  'rwins': 3,
                                  'note': 'Andy vs Eli 1'
                              })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'failure'
        assert 'msg' in response_json
        assert 'Eli is not entered' in response_json['msg']
        response = client.put('/ajax/bouts',
                              data={
                                  'action': 'add',
                                  'tourney_id': 1,
                                  'lplayer': 1,
                                  'rplayer': 5,
                                  'lwins': 1,
                                  'draws': 2,
                                  'rwins': 3,
                                  'note': 'Andy vs Eli 2'
                              })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'failure'
        assert 'msg' in response_json
        assert 'Eli is not entered' in response_json['msg']


def test_ajax_bouts_settings_get(client, app, auth):
    auth.login()
    with client:
        response = client.get('/ajax/bouts/settings?bout_id=2')
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        val_dict = response_json['value']
        assert 'dlg_html' in val_dict
        expected_dict = {
            'draws': 1,
            'form_name': 'bout_settings_dlg_form_2',
            'id': 2,
            'lplayer': 'Betty',
            'lplayer_id': 2,
            'lwins': 2,
            'note': 'tourney 1 set 2',
            'rplayer': 'Andy',
            'rplayer_id': 1,
            'rwins': 3,
            'tourney_id': 1
        }
        for key, val in expected_dict.items():
            assert val_dict.get(key, None) == val


def _get_values_for_bout(client, bout_id):
    response = client.get(f'/ajax/bouts/settings?bout_id={bout_id}')
    response_json = json.loads(response.data.decode('utf-8'))
    assert 'status' in response_json
    assert response_json['status'] == 'success'
    assert 'value' in response_json
    return response_json['value']


def _get_values_for_tourney(client, tourney_id):
    response = client.get(f'/ajax/tourneys/settings?tourney_id={tourney_id}')
    response_json = json.loads(response.data.decode('utf-8'))
    assert 'status' in response_json
    assert response_json['status'] == 'success'
    assert 'value' in response_json
    return response_json['value']


def test_ajax_bouts_settings_put(client, app, auth):
    bout_id = 2
    auth.login()
    with client:
        before_values = _get_values_for_bout(client, bout_id)
        change_dict = {
            'draws': 2,
            'lplayer': 3,
            'lwins': 3,
            'note': 'this note is new',
            'rplayer': 2,
            'rwins': 5,
        }
        for key, new_val in change_dict.items():
            response = client.put('/ajax/bouts/settings',
                                  data={
                                      'bout_id': bout_id,
                                      key: new_val
                                  })
            response_json = json.loads(response.data.decode('utf-8'))
            assert 'status' in response_json
            assert response_json['status'] == 'success'
            response_dict = response_json['value']
            mapped_key = {'lplayer': 'lplayer_id',
                          'rplayer': 'rplayer_id'}.get(key, key)
            assert response_dict[mapped_key] == new_val
            new_values = _get_values_for_bout(client, bout_id)
            assert new_values[mapped_key] == new_val
            before_values = new_values


def test_ajax_whoiswinning_post(client, app, auth):
    auth.login()
    with client:
        cbox_data = json.dumps({
            1: True,
            2: False,
            3: True
        })
        response = client.post('/ajax/whoiswinning',
                               data={
                                   'tourney_id': 1,
                                   'checkboxes': cbox_data
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        response_dict = response_json['value']
        assert 'announce_html' in response_dict
        assert 'dlg_html' in response_dict
        assert 'image' in response_dict
        assert 'label_str' in response_dict
        assert 'test_tourney_1' in response_dict['label_str']
        response = client.post('/ajax/whoiswinning',
                               data={
                                   'tourney_id': -1,
                                   'checkboxes': cbox_data
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        response_dict = response_json['value']
        assert 'announce_html' in response_dict
        assert 'dlg_html' in response_dict
        assert 'image' in response_dict
        assert 'label_str' in response_dict
        assert '5 tournaments' in response_dict['label_str']


def test_ajax_wfw_post(client, app, auth):
    auth.login()
    with client:
        cbox_data = json.dumps({
            1: True,
            2: False,
            3: True
        })
        response = client.post('/ajax/wfw',
                               data={
                                   'tourney_id': 1,
                                   'checkboxes': cbox_data
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        response_dict = response_json['value']
        assert 'dlg_html' in response_dict
        assert 'image' in response_dict
        assert 'label_str' in response_dict
        assert 'test_tourney_1' in response_dict['label_str']
        response = client.post('/ajax/wfw',
                               data={
                                   'tourney_id': -1,
                                   'checkboxes': cbox_data
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        response_dict = response_json['value']
        assert 'dlg_html' in response_dict
        assert 'image' in response_dict
        assert 'label_str' in response_dict
        assert '5 tournaments' in response_dict['label_str']


@pytest.mark.parametrize(('user_name', 'exists'),
                         (('other', True),
                          ('foo', False),
                          )
                         )
def test_ajax_admin_check_user_exists_post(client, app, auth,
                                           user_name, exists):
    auth.login(email='admin@foo.bar', password='AAA') # admin login
    with client:
        response = client.post('/ajax/admin/check_user_exists',
                               data={
                                   "user_name": user_name,
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        response_dict = response_json['value']
        assert 'exists' in response_dict
        assert 'user_name' in response_dict
        assert response_dict['exists'] == exists
        assert response_dict['user_name'] == user_name


@pytest.mark.parametrize(('group_name', 'exists'),
                         (('grouptwo', True),
                          ('fakegroup', False),
                          )
                         )
def test_ajax_admin_check_group_exists_post(client, app, auth,
                                            group_name, exists):
    auth.login(email='admin@foo.bar', password='AAA') # admin login
    with client:
        response = client.post('/ajax/admin/check_group_exists',
                               data={
                                   "group_name": group_name,
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        response_dict = response_json['value']
        assert 'exists' in response_dict
        assert 'group_name' in response_dict
        assert response_dict['exists'] == exists
        assert response_dict['group_name'] == group_name

        
def test_ajax_admin_add_group_post(client, app, auth):
    group_name = "new group"
    auth.login(email='admin@foo.bar', password='AAA') # admin login
    with client:
        response = client.post('/ajax/admin/check_group_exists',
                               data={
                                   "group_name": group_name,
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        response_dict = response_json['value']
        assert 'exists' in response_dict
        assert 'group_name' in response_dict
        assert response_dict['exists'] == False
        assert response_dict['group_name'] == group_name
        response = client.post('/ajax/admin/add_group',
                               data={
                                   "group_name": group_name,
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        response_dict = response_json['value']
        assert 'created' in response_dict
        assert 'group_name' in response_dict
        assert response_dict['created'] == True
        assert response_dict['group_name'] == group_name
        response = client.post('/ajax/admin/check_group_exists',
                               data={
                                   "group_name": group_name,
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        response_dict = response_json['value']
        assert 'exists' in response_dict
        assert 'group_name' in response_dict
        assert response_dict['exists'] == True
        assert response_dict['group_name'] == group_name
        response = client.post('/ajax/admin/add_group',
                               data={
                                   "group_name": group_name,
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        assert response_json['status'] == 'success'
        assert 'value' in response_json
        response_dict = response_json['value']
        assert 'created' in response_dict
        assert 'group_name' in response_dict
        assert response_dict['created'] == False
        assert response_dict['group_name'] == group_name


@pytest.mark.parametrize(('group_name', 'works', 'msg'),
                         (('nosuchgroup', False, 'No such group'),
                          ('everyone', False, 'The "everyone" group cannot'),
                          ('other', False, 'The group "other" cannot be deleted because it is'),
                          ('groupone', False, ('This group cannot be deleted because it is'
                                               ' associated with the following'
                                               ' tourneys: "test_tourney_8".')),
                          ('grouptwo', True, ''),
                          )
                         )
def test_ajax_admin_remove_group_post(client, app, auth, group_name, works, msg):
    auth.login(email='admin@foo.bar', password='AAA') # admin login
    with client:
        response = client.post('/ajax/admin/remove_group',
                               data={
                                   "group_name": group_name,
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        pprint(response_json)
        assert 'status' in response_json
        if works:
            assert response_json['status'] == 'success'
            assert 'value' in response_json
            response_dict = response_json['value']
            assert 'removed' in response_dict
            assert response_dict['removed'] == True
            assert 'group_name' in response_dict
            assert response_dict['group_name'] == group_name
            response = client.post('/ajax/admin/check_group_exists',
                                   data={
                                       "group_name": group_name,
                                   })
            response_json = json.loads(response.data.decode('utf-8'))
            assert 'status' in response_json
            assert response_json['status'] == 'success'
            assert 'value' in response_json
            response_dict = response_json['value']
            assert 'exists' in response_dict
            assert 'group_name' in response_dict
            assert response_dict['exists'] == False
            assert response_dict['group_name'] == group_name
        else:
            assert response_json['status'] == 'failure'
            assert 'msg' in response_json
            assert response_json['msg'].startswith(msg)


@pytest.mark.parametrize(('user_name', 'works', 'group_names'),
                         (('nosuchuser', False, []),
                          ('other', True, ['other', 'everyone', 'grouptwo']),
                          )
                         )
def test_ajax_admin_get_user_groups_post(client, app, auth, user_name, works, group_names):
    auth.login(email='admin@foo.bar', password='AAA') # admin login
    with client:
        response = client.post('/ajax/admin/get_user_groups',
                               data={
                                   "user_name": user_name,
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        pprint(response_json)
        assert 'status' in response_json
        if works:
            assert response_json['status'] == 'success'
            assert 'value' in response_json
            response_dict = response_json['value']
            assert 'user_name' in response_dict
            assert response_dict['user_name'] == user_name
            assert 'groups' in response_dict
            assert set(response_dict['groups']) == set(group_names)
        else:
            assert response_json['status'] == 'failure'
            assert 'msg' in response_json
            assert response_json['msg'] == f'No such user "{user_name}"'


@pytest.mark.parametrize(('user_name', 'group_name', 'works', 'msg'),
                         (('nosuchuser', 'groupone', False, 'No such user'),
                          ('other', 'nosuchgroup', False, 'No such group'),
                          ('other', 'groupone', True, ''),
                          ('other', 'grouptwo', True, ''),
                          )
                         )
def test_ajax_admin_add_user_to_group_post(client, app, auth, user_name, group_name, works, msg):
    auth.login(email='admin@foo.bar', password='AAA') # admin login
    with client:
        if works:
            response = client.post('/ajax/admin/get_user_groups',
                                   data={
                                       "user_name": user_name,
                                   })
            response_json = json.loads(response.data.decode('utf-8'))
            before_set = set(response_json['value']['groups'])
        else:
            before_set = set([])
        response = client.post('/ajax/admin/add_user_to_group',
                               data={
                                   "user_name": user_name,
                                   "group_name": group_name,
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        pprint(response_json)
        if works:
            assert response_json['status'] == 'success'
            assert 'value' in response_json
            response_dict = response_json['value']
            assert 'user_name' in response_dict
            assert response_dict['user_name'] == user_name
            assert 'group_name' in response_dict
            assert response_dict['group_name'] == group_name
            assert 'added' in response_dict
            assert response_dict['added'] == (group_name not in before_set)
            response = client.post('/ajax/admin/get_user_groups',
                                   data={
                                       "user_name": user_name,
                                   })
            response_json = json.loads(response.data.decode('utf-8'))
            after_set = set(response_json['value']['groups'])
            assert group_name in after_set
        else:
            assert response_json['status'] == 'failure'
            assert 'msg' in response_json
            assert response_json['msg'].startswith(msg)


@pytest.mark.parametrize(('user_name', 'group_name', 'works', 'msg'),
                         (('nosuchuser', 'groupone', False, 'No such user'),
                          ('other', 'nosuchgroup', False, 'No such group'),
                          ('other', 'everyone', False, 'Everyone should be in the group "everyone"'),
                          ('other', 'other', False, 'Everyone should be in their personal group'),
                          ('other', 'groupone', False, '"other" is not a member'),
                          ('other', 'grouptwo', True, ''),
                          )
                         )
def test_ajax_admin_remove_user_from_group_post(client, app, auth, user_name, group_name, works, msg):
    auth.login(email='admin@foo.bar', password='AAA') # admin login
    with client:
        if works:
            response = client.post('/ajax/admin/get_user_groups',
                                   data={
                                       "user_name": user_name,
                                   })
            response_json = json.loads(response.data.decode('utf-8'))
            before_set = set(response_json['value']['groups'])
        else:
            before_set = set([])
        response = client.post('/ajax/admin/remove_user_from_group',
                               data={
                                   "user_name": user_name,
                                   "group_name": group_name,
                               })
        response_json = json.loads(response.data.decode('utf-8'))
        assert 'status' in response_json
        pprint(response_json)
        if works:
            assert response_json['status'] == 'success'
            assert 'value' in response_json
            response_dict = response_json['value']
            assert 'user_name' in response_dict
            assert response_dict['user_name'] == user_name
            assert 'group_name' in response_dict
            assert response_dict['group_name'] == group_name
            assert 'removed' in response_dict
            assert response_dict['removed'] == (group_name in before_set)
            response = client.post('/ajax/admin/get_user_groups',
                                   data={
                                       "user_name": user_name,
                                   })
            response_json = json.loads(response.data.decode('utf-8'))
            after_set = set(response_json['value']['groups'])
            assert group_name not in after_set
        else:
            assert response_json['status'] == 'failure'
            assert 'msg' in response_json
            assert response_json['msg'].startswith(msg)

