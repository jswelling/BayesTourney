import pytest
from bayestourney.database import get_db
from bayestourney.models import User, Group, Tourney, LogitPlayer, TourneyPlayerPair
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

