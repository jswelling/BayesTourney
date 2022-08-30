#! /usr/bin/env python

from typing import Iterable

from flask_login import current_user

from .database import get_db
from .models import User, Group, Tourney


class PermissionException(Exception):
    pass


def current_user_can_read(tourney: Tourney) -> bool:
    if current_user.admin:
        return True
    elif tourney.owner == current_user.id and tourney.owner_read:
        return True
    elif (tourney.group in [grp.id
                            for grp in current_user.get_groups(get_db())]
          and tourney.group_read):
        return True
    elif tourney.other_read:
        return True
    return False


def current_user_can_write(tourney: Tourney) -> bool:
    if current_user.admin:
        return True
    elif tourney.owner == current_user.id and tourney.owner_write:
        return True
    elif (tourney.group in [grp.id
                            for grp in current_user.get_groups(get_db())]
          and tourney.group_write):
        return True
    elif tourney.other_write:
        return True
    return False


def current_user_can_delete(tourney: Tourney) -> bool:
    if current_user.admin:
        return True
    elif tourney.owner == current_user.id and tourney.owner_delete:
        return True
    elif (tourney.group in [grp.id
                            for grp in current_user.get_groups(get_db())]
          and tourney.group_delete):
        return True
    elif tourney.other_delete:
        return True
    return False


def check_can_read(tourney: Tourney) -> None:
    if not current_user_can_read(tourney):
        msg = (f"{current_user.username} does not have read"
               f" access to the tournament {tourney.name}")
        raise PermissionException(msg)


def check_can_write(tourney: Tourney) -> None:
    if not current_user_can_write(tourney):
        msg = (f"{current_user.username} does not have write"
               f" access to the tournament {tourney.name}")
        raise PermissionException(msg)


def check_can_delete(tourney: Tourney) -> None:
    if not current_user_can_delete(tourney):
        msg = (f"{current_user.username} does not have delete"
               f" access to the tournament {tourney.name}")
        raise PermissionException(msg)


def get_readable_tourneys(db) -> Iterable[Tourney]:
    tourneyList1 = db.query(Tourney).filter_by(owner=current_user.id)
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
    
