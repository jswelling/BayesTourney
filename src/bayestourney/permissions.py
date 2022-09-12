#! /usr/bin/env python

from typing import Iterable, Union

from flask_login import current_user

from .database import get_db
from .models import User, Group, Tourney, LogitPlayer


class PermissionException(Exception):
    pass


def current_user_can_read(tourney_or_player: Union[Tourney, LogitPlayer],
                          **kwargs) -> bool:
    if isinstance(tourney_or_player, Tourney):
        tourney = tourney_or_player
        owner_read = kwargs.get('owner_read', tourney.owner_read)
        group_read = kwargs.get('group_read', tourney.group_read)
        other_read = kwargs.get('other_read', tourney.other_read)
        if 'group_name' in kwargs:
            group_id = (get_db().query(Group).filter_by(name=kwargs['group_name'])
                        .one().id)
        else:
            group_id = tourney.group
        if current_user.admin:
            return True
        elif tourney.owner == current_user.id and owner_read:
            return True
        elif (group_id in [grp.id for grp in current_user.get_groups(get_db())]
              and group_read):
            return True
        elif other_read:
            return True
        return False
    else:
        return True  # only tourneys are currently checked for permissions


def current_user_can_write(tourney_or_player: Union[Tourney, LogitPlayer],
                           **kwargs) -> bool:
    if isinstance(tourney_or_player, Tourney):
        tourney = tourney_or_player
        owner_write = kwargs.get('owner_write', tourney.owner_write)
        group_write = kwargs.get('group_write', tourney.group_write)
        other_write = kwargs.get('other_write', tourney.other_write)
        if 'group_name' in kwargs:
            group_id = (get_db().query(Group).filter_by(name=kwargs['group_name'])
                        .one().id)
        else:
            group_id = tourney.group
        if current_user.admin:
            return True
        elif tourney.owner == current_user.id and owner_write:
            return True
        elif (group_id in [grp.id for grp in current_user.get_groups(get_db())]
              and group_write):
            return True
        elif other_write:
            return True
        return False
    else:
        return True  # only tourneys are currently checked for permissions


def current_user_can_delete(tourney_or_player: Union[Tourney, LogitPlayer],
                            **kwargs) -> bool:
    if isinstance(tourney_or_player, Tourney):
        tourney = tourney_or_player
        owner_delete = kwargs.get('owner_delete', tourney.owner_delete)
        group_delete = kwargs.get('group_delete', tourney.group_delete)
        other_delete = kwargs.get('other_delete', tourney.other_delete)
        if 'group_name' in kwargs:
            group_id = (get_db().query(Group).filter_by(name=kwargs['group_name'])
                        .one().id)
        else:
            group_id = tourney.group
        if current_user.admin:
            return True
        elif tourney.owner == current_user.id and owner_delete:
            return True
        elif (group_id in [grp.id for grp in current_user.get_groups(get_db())]
              and group_delete):
            return True
        elif other_delete:
            return True
        return False
    else:
        return True  # only tourneys are currently checked for permissions


def check_can_read(tourney_or_player: Union[Tourney, LogitPlayer]) -> None:
    if not current_user_can_read(tourney_or_player):
        msg = (f"{current_user.username} does not have read"
               f" access to {tourney_or_player.name}")
        raise PermissionException(msg)


def check_can_write(tourney_or_player: Union[Tourney, LogitPlayer]) -> None:
    if not current_user_can_write(tourney_or_player):
        msg = (f"{current_user.username} does not have write"
               f" access to {tourney_or_player.name}")
        raise PermissionException(msg)


def check_can_delete(tourney_or_player: Union[Tourney, LogitPlayer]) -> None:
    if not current_user_can_delete(tourney_or_player):
        msg = (f"{current_user.username} does not have delete"
               f" access to {tourney_or_player.name}")
        raise PermissionException(msg)


def get_readable_tourneys(db) -> Iterable[Tourney]:
    tourneyList1 = (db.query(Tourney)
                    .filter(Tourney.owner == current_user.id,
                            Tourney.owner_read == True)
                    )
    group_id_list = [gp.id for gp in current_user.get_groups(db)]
    tourneyList2 = (db.query(Tourney)
                    .filter(Tourney.group.in_(group_id_list),
                            Tourney.group_read == True)
                    )
    tourneyList3 = db.query(Tourney).filter_by(other_read=True)
    tourneyList = (tourneyList1
                   .union(tourneyList2)
                   .union(tourneyList3)
                   .all()
                   )
    return tourneyList
    
