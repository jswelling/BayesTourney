import pytest
from bayestourney.database import get_db
from bayestourney.models import User, Group, Tourney, LogitPlayer
from sqlalchemy.exc import IntegrityError
from bayestourney.permissions import (PermissionException,
                                      get_readable_tourneys,
                                      get_readable_players,
                                      current_user_can_read,
                                      current_user_can_write,
                                      current_user_can_delete,
                                      check_can_read,
                                      check_can_write,
                                      check_can_delete
                                      )

def test_perms_on_creation(app):
    with app.app_context():
        db = get_db()
        user = db.query(User).filter_by(id=1).one()
        group = db.query(Group).filter_by(name=user.username).one()
        tourney = Tourney('new_test_tourney', user.id, group.id,
                          permissions={'other_read':True, 'group_write':True})
        db.add(tourney)
        db.commit()
        tourney = db.query(Tourney).filter_by(name='new_test_tourney').one()
        print(f"USER PERMS {tourney.owner_write} {tourney.owner_read} {tourney.owner_delete}")
        print(f"GROUP PERMS {tourney.group_write} {tourney.group_read} {tourney.group_delete}")
        print(f"OTHER PERMS {tourney.other_write} {tourney.other_read} {tourney.other_delete}")
        assert tourney.owner_write == True
        assert tourney.owner_read == True
        assert tourney.owner_delete == True
        assert tourney.group_write == True
        assert tourney.group_read == True
        assert tourney.group_delete == False
        assert tourney.other_write == False
        assert tourney.other_read == True
        assert tourney.other_delete == False


def test_permission_bool_funcs(app, client, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
        db = get_db()
        for name, readable, writeable, delable in [
                ('test_tourney_1', True, True, True),
                ('test_tourney_2', True, True, True),
                ('test_tourney_3', False, False, False),
                ('test_tourney_4', True, False, False),
                ('test_tourney_5', False, False, False),
                ('test_tourney_6', True, True, True),
                ('test_tourney_7', True, True, True),
                ]:
            tourney = db.query(Tourney).filter_by(name=name).one()
            assert current_user_can_read(tourney) == readable
            assert current_user_can_write(tourney) == writeable
            assert current_user_can_delete(tourney) == delable


def test_player_permission_bool_funcs(app, client, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
        db = get_db()
        for name, readable, writeable, delable in [
                ('Andy', True, True, True),
                ]:
            player = db.query(LogitPlayer).filter_by(name=name).one()
            assert current_user_can_read(player) == readable
            assert current_user_can_write(player) == writeable
            assert current_user_can_delete(player) == delable


def test_permission_exceptions(app, client, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
        db = get_db()
        for name, readable, writeable, delable in [
                ('test_tourney_1', True, True, True),
                ('test_tourney_2', True, True, True),
                ('test_tourney_3', False, False, False),
                ('test_tourney_4', True, False, False),
                ('test_tourney_5', False, False, False),
                ('test_tourney_6', True, True, True),
                ('test_tourney_7', True, True, True),
                ]:
            tourney = db.query(Tourney).filter_by(name=name).one()
            if readable:
                check_can_read(tourney)
            else:
                with pytest.raises(PermissionException) as excinfo:
                    check_can_read(tourney)
                assert name in str(excinfo.value)
                assert 'read' in str(excinfo.value)
            if writeable:
                check_can_write(tourney)
            else:
                with pytest.raises(PermissionException) as excinfo:
                    check_can_write(tourney)
                assert name in str(excinfo.value)
                assert 'write' in str(excinfo.value)
            if delable:
                check_can_delete(tourney)
            else:
                with pytest.raises(PermissionException) as excinfo:
                    check_can_delete(tourney)
                assert name in str(excinfo.value)
                assert 'delete' in str(excinfo.value)


def test_player_permission_exceptions(app, client, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
        db = get_db()
        for name, readable, writeable, delable in [
                ('Andy', True, True, True),
                ]:
            player = db.query(LogitPlayer).filter_by(name=name).one()
            if readable:
                check_can_read(player)
            else:
                with pytest.raises(PermissionException) as excinfo:
                    check_can_read(player)
                assert name in str(excinfo.value)
                assert 'read' in str(excinfo.value)
            if writeable:
                check_can_write(player)
            else:
                with pytest.raises(PermissionException) as excinfo:
                    check_can_write(player)
                assert name in str(excinfo.value)
                assert 'write' in str(excinfo.value)
            if delable:
                check_can_delete(player)
            else:
                with pytest.raises(PermissionException) as excinfo:
                    check_can_delete(player)
                assert name in str(excinfo.value)
                assert 'delete' in str(excinfo.value)


def test_get_readable_tourneys(app, client, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
        db = get_db()
        tourney_list = get_readable_tourneys(db)
        for tourney in tourney_list:
            assert current_user_can_read(tourney)


def test_get_readable_players(app, client, auth):
    auth.login()
    with client:
        client.get('/')  # forces current_user to have a value
        db = get_db()
        player_list = get_readable_players(db)
        for player in player_list:
            assert current_user_can_read(player)
