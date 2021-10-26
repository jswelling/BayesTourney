import pytest
import json
from pprint import pprint
from flask import g, session
from bayestourney.database import get_db
from .test_endpoints import parse_jqgrid_response_json
from bayestourney.settings_constants import ALLOWED_SETTINGS, DEFAULT_SETTINGS


def test_settings_get_default(auth, client, app):
    auth.login()
    with client:
        response = client.get('/ajax/settings')
        assert response.status_code == 200
        response_json = json.loads(response.data.decode('utf-8').strip())
        with open('/tmp/debug.txt','w') as f:
            pprint(response_json, stream=f)
        for key, val in DEFAULT_SETTINGS.items():
            assert response_json['value'][key] == val

def test_settings_put_get(auth, client, app):
    auth.login()
    with client:
        for key, val_list in ALLOWED_SETTINGS.items():
            for val in val_list:
                put_response = client.put('/ajax/settings' + '?name=' + key + '&id=' + val)
                assert put_response.status_code == 200
                put_response_json = json.loads(put_response.data.decode('utf-8').strip())
                assert put_response_json['status'] == 'success'
                response = client.get('/ajax/settings')
                assert response.status_code == 200
                response_json = json.loads(response.data.decode('utf-8').strip())
                assert response_json['value'][key] == val

def test_settings_put_invalid(auth, client, app):
    auth.login()
    with client:
        put_response = client.put('/ajax/settings' + '?name=foo&id=bar')
        assert put_response.status_code == 200
        put_response_json = json.loads(put_response.data.decode('utf-8').strip())
        assert 'status' in put_response_json
        assert 'msg' in put_response_json
        assert put_response_json['status'] == 'error'
        assert 'foo' in put_response_json['msg']
        put_response = client.put('/ajax/settings' + '?name=hr_graph_style&id=bar')
        assert put_response.status_code == 200
        put_response_json = json.loads(put_response.data.decode('utf-8').strip())
        assert 'status' in put_response_json
        assert 'msg' in put_response_json
        assert put_response_json['status'] == 'error'
        assert 'bar' in put_response_json['msg']
        # for key, val_list in ALLOWED_SETTINGS.items():
        #     for val in val_list:
        #         put_response_json = json.loads(put_response.data.decode('utf-8').strip())
        #         assert put_response_json['status'] == 'success'
        #         response = client.get('/ajax/settings')
        #         assert response.status_code == 200
        #         response_json = json.loads(response.data.decode('utf-8').strip())
        #         assert response_json['value'][key] == val
