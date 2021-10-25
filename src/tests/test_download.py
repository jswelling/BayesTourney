import pytest
import json
import pandas as pd
from io import BytesIO
from pprint import pprint
from flask import g, session, url_for
from bayestourney.database import get_db
from .test_endpoints import _parse_jqgrid_response_json

def _get_rec_dict(client, endpoint):
    response = client.get(endpoint)
    assert response.status_code == 200
    return _parse_jqgrid_response_json(json.loads(response.data.decode('utf-8')))


def test_download_entrants(auth, client, app):
    auth.login()
    with client:
        before_dict = _get_rec_dict(client, '/json/entrants?tourneyId=2')
        response =client.get(
            '/download/entrants' + '?tourney=2',
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert response.headers['Content-Disposition'] == 'attachment; filename=entrants.tsv'
        test_df = pd.read_csv(BytesIO(response.data), sep='\t')
        compare_recs = [[rec[1], rec[4]] for rec in before_dict.values()]
        for idx, row in test_df.iterrows():
            assert [row['name'], row['note']] in compare_recs
        

def test_download_entrants(auth, client, app):
    auth.login()
    with client:
        before_dict = _get_rec_dict(client, '/json/entrants?tourneyId=2')
        response =client.get(
            '/download/entrants' + '?tourney=2',
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert response.headers['Content-Disposition'] == 'attachment; filename=entrants.tsv'
        test_df = pd.read_csv(BytesIO(response.data), sep='\t')
        compare_recs = [[rec[1], rec[4]] for rec in before_dict.values()]
        for idx, row in test_df.iterrows():
            assert [row['name'], row['note']] in compare_recs



def test_download_bouts(auth, client, app):
    auth.login()
    with client:
        before_dict = _get_rec_dict(client, '/json/bouts?tourneyId=2')
        response =client.get(
            '/download/bouts' + '?tourney=2',
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert response.headers['Content-Disposition'] == 'attachment; filename=bouts.tsv'
        test_df = pd.read_csv(BytesIO(response.data), sep='\t')
        compare_recs = [[rec[0], rec[2], rec[4], rec[6]] for rec in before_dict.values()]
        for idx, row in test_df.iterrows():
            test_rec = [row['tourneyName'], row['leftPlayerName'],
                        row['rightPlayerName'], row['note']]
            assert test_rec in compare_recs


        