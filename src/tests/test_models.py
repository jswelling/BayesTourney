import pytest
from bayestourney.database import get_db
from bayestourney.models import (User, Group, Tourney, LogitPlayer,
                                 TourneyPlayerPair, DBException)
from sqlalchemy.exc import IntegrityError


def test_group(app):
    with app.app_context():
        db = get_db()
        groups = db.query(Group)
        orig_group_set = set(gp.name for gp in groups)
        new_names = ['mygroupname', 'othergroupname']
        for nm in new_names:
            db.add(Group(nm))
        db.commit()
        groups = db.query(Group)
        after_group_set = set(gp.name for gp in groups)
        assert after_group_set ^ orig_group_set == set(new_names)
        with pytest.raises(IntegrityError) as excinfo:
            new_group = Group('mygroupname')
            db.add(new_group)
            db.commit()
        assert 'UNIQUE constraint failed' in str(excinfo.value)


def test_group_2(app):
    with app.app_context():
        db = get_db()
        group = db.query(Group).filter_by(name='everyone').one()
        users = group.get_users(db)
        pre_user_set = set(user.username for user in users)
        assert all(nm in pre_user_set for nm in ['test', 'other'])
        group.add_user(db, db.query(User).filter_by(username='admin').one())
        db.commit()
        users = group.get_users(db)
        post_user_set = set(user.username for user in users)
        change_set = post_user_set - pre_user_set
        assert change_set == set(['admin'])


def test_user_group_pair(app):
    with app.app_context():
        db = get_db()
        user = db.query(User).filter_by(username='test').one()
        groups = user.get_groups(db)
        grp_nm_set = set(gp.name for gp in groups)
        for nm in ['test', 'everyone']:
            assert nm in grp_nm_set
        new_group = Group('someothername')
        db.add(new_group)
        db.commit()
        user.add_group(db, new_group)
        db.commit()
        new_nm_set = set(gp.name for gp in user.get_groups(db))
        assert new_nm_set ^ grp_nm_set == set(['someothername'])
        user.remove_group(db, new_group)
        db.commit()
        after_del_nm_set = set(gp.name for gp in user.get_groups(db))
        assert after_del_nm_set == grp_nm_set


def test_player_tourney_pair(app):
    with app.app_context():
        db = get_db();
        pairs = db.query(TourneyPlayerPair).all()
        expected_initial_pairs = [(1, 1), (1, 2), (1, 3), (2, 2), (2, 3)]
        pair_set = set((pair.tourney_id, pair.player_id) for pair in pairs)
        assert len(pairs) == len(expected_initial_pairs)
        for pair in expected_initial_pairs:
            assert pair in pair_set
        tourney = db.query(Tourney).filter(Tourney.tourneyId == 3).one()
        player_list = tourney.get_players(db)
        assert len(player_list) == 0
        player = db.query(LogitPlayer).filter(LogitPlayer.id == 4).one()
        tourney.add_player(db, player)
        db.commit()
        player_list = tourney.get_players(db)
        assert len(player_list) == 1
        assert player_list[0].id == 4
        player = db.query(LogitPlayer).filter(LogitPlayer.id == 4).one()
        tourney.remove_player(db, player)
        db.commit()
        player_list = tourney.get_players(db)
        assert len(player_list) == 0
        player = db.query(LogitPlayer).filter(LogitPlayer.id == 2).one()
        tourney_list = player.get_tourneys(db)
        tourney_set = set(tourney.tourneyId for tourney in tourney_list)
        assert tourney_set == set([1, 2])
        player = db.query(LogitPlayer).filter(LogitPlayer.id == 4).one()
        tourney = db.query(Tourney).filter(Tourney.tourneyId == 3).one()
        player_list = tourney.get_players(db)
        assert len(player_list) == 0
        player.add_tourney(db, tourney)
        db.commit()
        player_list = tourney.get_players(db)
        assert len(player_list) == 1
        assert player_list[0].name == 'Donna'
        player.add_tourney(db, tourney)
        db.commit()
        player_list = tourney.get_players(db)
        assert len(player_list) == 1
        assert player_list[0].name == 'Donna'


def test_player(app):
    with app.app_context():
        db = get_db()
        initial_player_name_set = set(player.name for player in
                                      db.query(LogitPlayer).all())
        new_player = LogitPlayer.create_unique(db, 'SomeRandomGuy', 'Here is a note')
        db.commit()
        new_player_name_set = set(player.name for player in
                                  db.query(LogitPlayer).all())
        change_set = new_player_name_set - initial_player_name_set
        assert len(change_set) == 1
        assert 'SomeRandomGuy' in change_set
        initial_player_name_set = new_player_name_set
        with pytest.raises(DBException) as excinfo:
            new_player = LogitPlayer.create_unique(db, 'SomeRandomGuy',
                                                   'Here is a different note')
            db.commit()
        assert 'SomeRandomGuy' in str(excinfo.value)
        new_player_name_set = set(player.name for player in
                                  db.query(LogitPlayer).all())
        assert initial_player_name_set == new_player_name_set  # duplicate rejected
        player = db.query(LogitPlayer).filter_by(name='SomeRandomGuy').one()
        assert player.as_dict(include_id=False) == {'name': 'SomeRandomGuy',
                                                    'note': 'Here is a note'}
        assert player.as_dict(include_id=True) == {'name': 'SomeRandomGuy',
                                                   'note': 'Here is a note',
                                                   'id': player.id}


def test_tourney(app, client, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
        with app.app_context():
            db = get_db();
            initial_tourney_name_set = set(tourney.name for tourney in
                                           db.query(Tourney).all())
            with pytest.raises(DBException) as excinfo:
                tourney = Tourney.create_unique(db, 'test_tourney_1', 'this should fail')
            assert 'test_tourney_1' in str(excinfo)
            assert 'exists' in str(excinfo)
            tourney = Tourney.create_unique(db, 'some unique name', 'this should not fail')
            assert 'some unique name' in str(tourney)
