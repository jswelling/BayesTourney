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

    
