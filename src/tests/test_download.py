import pytest
import json
import pandas as pd
from io import BytesIO
from pprint import pprint
from flask import g, session, url_for
from bayestourney.database import get_db
from .test_endpoints import parse_jqgrid_response_json
from .test_upload import get_rec_dict, get_ajax_rec_dict

@pytest.mark.parametrize(('tourney_id','tourney_label'),
                         ((2, 'test_tourney_2'),
                          (-1, 'ALL_TOURNEYS')))
def test_download_entrants(auth, client, app, tourney_id, tourney_label):
    auth.login()
    with client:
        before_dict = get_rec_dict(client, f'/json/entrants?tourneyId={tourney_id}')
        response =client.get(
            '/download/entrants' + f'?tourney_id={tourney_id}',
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert response.headers['Content-Disposition'] == f'attachment; filename=entrants_{tourney_label}.tsv'
        test_df = pd.read_csv(BytesIO(response.data), sep='\t')
        compare_recs = [[rec[1], rec[4]] for rec in before_dict.values()]
        for idx, row in test_df.iterrows():
            assert [row['name'], row['note']] in compare_recs
        

@pytest.mark.parametrize(('tourney_id', 'fname'),((2, 'test_tourney_2'),(-1,'ALL_TOURNEYS')))
def test_download_bouts(auth, client, app, tourney_id, fname):
    auth.login()
    with client:
        before_dict = get_rec_dict(client, f'/json/bouts?tourney_id={tourney_id}')
        response = client.get(
            '/download/bouts' + f'?tourney_id={tourney_id}',
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert response.headers['Content-Disposition'] == f'attachment; filename=bouts_{fname}.tsv'
        test_df = pd.read_csv(BytesIO(response.data), sep='\t')
        compare_recs = [[rec[0], rec[2], rec[4], rec[6]] for rec in before_dict.values()]
        for idx, row in test_df.iterrows():
            test_rec = [row['tourneyName'], row['leftPlayerName'],
                        row['rightPlayerName'], row['note']]
            assert test_rec in compare_recs


@pytest.mark.parametrize(('tourney_id', 'fname'),((2, 'test_tourney_2'),(-1,'ALL_TOURNEYS')))
def test_download_bearpit(auth, client, app, tourney_id, fname):
    auth.login()
    with client:
        before_dict = get_ajax_rec_dict(client, f'/ajax/bearpit?tourney_id={tourney_id}')
        response = client.get(
            f'/download/horserace?tourney_id={tourney_id}',
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert response.headers['Content-Disposition'] == f'attachment; filename=bearpit_{fname}.tsv'
        test_df = pd.read_csv(BytesIO(response.data), sep='\t')
        for idx, row in test_df.iterrows():
            test_rec = {
                'name': row['playerName'],
                'id': row['id'],
                'wins': row['wins'],
                'losses': row['losses'],
                'draws': row['draws'],
                'bearpit': row['bearpit'],
                'include': 1 if row['include'] else 0
            }
            assert test_rec == before_dict[row['id']]
