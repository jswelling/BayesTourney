from datetime import datetime

from sqlalchemy import (Column, Integer, Float, String, ForeignKey, JSON,
                        DateTime, Boolean)
from sqlalchemy import select
from sqlalchemy.orm import Query, column_property

from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash

from .database import Base

class DBException(Exception):
    pass

class User(UserMixin, Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    date_registered = Column(DateTime, default=datetime.utcnow)
    admin = Column(Boolean, nullable=False, default=False)
    confirmed = Column(Boolean, nullable=False, default=False)
    confirmed_on = Column(DateTime, nullable=True)
    prefs = Column(JSON, nullable=True)
    remember_me = Column(Boolean, nullable=False, default=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)

    def __str__(self):
        return "<User(%s)>"%self.username

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_groups(self, db):
        return (db.query(Group).join(UserGroupPair)
                .filter(UserGroupPair.user_id == self.id)
                .all())

    def add_group(self, db, group):
        if (db.query(UserGroupPair)
            .filter(UserGroupPair.user_id == self.id,
                    UserGroupPair.group_id == group.id)
            .first()) is None:
            db.add(UserGroupPair(self.id, group.id))

    def remove_group(self, db, group):
        (db.query(UserGroupPair)
         .filter(UserGroupPair.user_id == self.id,
                 UserGroupPair.group_id == group.id
                 )
         .delete())


class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return(f'<Group({self.id}, name={self.name})>')

    def get_users(self, db):
        return (db.query(User).join(UserGroupPair)
                .filter(UserGroupPair.group_id == self.id)
                .all())

    def add_user(self, db, user):
        if (db.query(UserGroupPair)
            .filter(UserGroupPair.group_id == self.id,
                    UserGroupPair.user_id == user.id)
            .first()) is None:
            db.add(UserGroupPair(user.id, self.id))


class UserGroupPair(Base):
    __tablename__ = "user_group_pair"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer,
                     ForeignKey('user.id', name='user_group_pair_user_id_constraint'),
                     nullable=False, index=True)
    group_id = Column(Integer,
                      ForeignKey('group.id', name='user_group_pair_group_id_constraint'),
                      nullable=False, index=True)

    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id


class Tourney(Base):
    __tablename__ = 'tourneys'
    tourneyId = Column(Integer, primary_key=True)
    name = Column(String)
    note = Column(String)
    owner = Column(Integer, ForeignKey('user.id', name='tourney_owner_id_constraint'))
    group = Column(Integer, ForeignKey('group.id', name='tourney_group_id_constraint'))
    owner_read = Column(Boolean)
    owner_write = Column(Boolean)
    owner_delete = Column(Boolean)
    group_read = Column(Boolean)
    group_write = Column(Boolean)
    group_delete = Column(Boolean)
    other_read = Column(Boolean)
    other_write = Column(Boolean)
    other_delete = Column(Boolean)
    ownerName = column_property(select([User.username]).where(User.id==owner)
                                .scalar_subquery())
    groupName = column_property(select([Group.name]).where(Group.id==group)
                                .scalar_subquery())
    
    def __init__(self, name, owner, group, note='', permissions={}):
        self.name = name
        self.owner = owner
        self.group = group
        self.note = note
        all_permissions = {
            'owner_read': True, 'owner_write': True, 'owner_delete': True,
            'group_read': True, 'group_write': False, 'group_delete': False,
            'other_read': False, 'other_write': False, 'other_delete': False,
            }
        all_permissions.update(permissions)
        for key in all_permissions:
            setattr(self, key, all_permissions[key])
        
    def __str__(self):
        return "<Tourney(%s) owned by %s, group %s>"%(self.name,
                                                      self.ownerName, self.groupName)

    def add_player(self, db, player):
        if (db.query(TourneyPlayerPair)
            .filter(TourneyPlayerPair.tourney_id == self.tourneyId,
                    TourneyPlayerPair.player_id == player.id)
            .first()) is None:
            db.add(TourneyPlayerPair(self.tourneyId, player.id))

    def remove_player(self, db, player):
        (db.query(TourneyPlayerPair)
         .filter(TourneyPlayerPair.tourney_id == self.tourneyId,
                 TourneyPlayerPair.player_id == player.id
                 )
         .delete())

    def get_players(self, db):
        return (db.query(LogitPlayer).join(TourneyPlayerPair)
                .filter(TourneyPlayerPair.tourney_id == self.tourneyId)
                .all())


class LogitPlayer(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    note = Column(String)
    
    def __init__(self,name,note):
        self.name = name
        self.note = note

    def __str__(self): return f"<LogitPlayer({self.name})>"

    @classmethod
    def create_unique(cls, db, name, note):
        if db.query(LogitPlayer).filter_by(name=name).first() is not None:
            raise DBException(f"A player with the name '{name}' already exists.")
        player = LogitPlayer(name, note)
        db.add(player)
        return player

    def fight(self,otherPlayer):
        raise RuntimeError('since LogitPlayer no longer has a weight,'
                           ' fight is no longer implemented')

    def get_tourneys(self, db):
        return (db.query(Tourney).join(TourneyPlayerPair)
                .filter(TourneyPlayerPair.player_id == self.id)
                .all())

    def add_tourney(self, db, tourney):
        if (db.query(TourneyPlayerPair)
            .filter(TourneyPlayerPair.tourney_id == tourney.tourneyId,
                    TourneyPlayerPair.player_id == self.id)
            .first()) is None:
            db.add(TourneyPlayerPair(tourney.tourneyId, self.id))

    def as_dict(self, include_id=True):
        if include_id:
            return {'id': self.id, 'name': self.name, 'note': self.note}
        else:
            return {'name': self.name, 'note': self.note}

        
class TourneyPlayerPair(Base):
    __tablename__ = "player_tourney_pair"
    id = Column(Integer, primary_key=True)
    tourney_id = Column(Integer,
                        ForeignKey('tourneys.tourneyId',
                                   name='tourney_player_pair_tourney_id_constraint'),
                        nullable=False, index=True)
    player_id = Column(Integer,
                       ForeignKey('players.id',
                                  name='tourney_player_pair_player_id_constraint'),
                       nullable=False, index=True)

    def __init__(self, tourney_id, player_id):
        self.tourney_id = tourney_id
        self.player_id = player_id

    def __str__(self):
        return f"<TourneyPlayerPair(tourney={self.tourney_id}, player={self.player_id})>"


class Bout(Base):
    __tablename__ = 'bouts'
    boutId = Column(Integer, primary_key=True)
    tourneyId = Column(Integer, ForeignKey('tourneys.tourneyId'))
    leftWins = Column(Integer)
    leftPlayerId = Column(Integer, ForeignKey('players.id'))
    rightPlayerId = Column(Integer, ForeignKey('players.id'))
    rightWins = Column(Integer)
    draws = Column(Integer)
    note = Column(String)
    lName = column_property(select([LogitPlayer.name]).where(LogitPlayer.id==leftPlayerId)
                            .scalar_subquery())
    rName = column_property(select([LogitPlayer.name]).where(LogitPlayer.id==rightPlayerId)
                            .scalar_subquery())
    tourneyName = column_property(select([Tourney.name]).where(Tourney.tourneyId==tourneyId)
                                  .scalar_subquery())
    def __init__(self, tourneyId, lWins,leftId, draws, rightId, rWins, note=""):
        self.tourneyId = tourneyId
        self.leftWins = lWins
        self.leftPlayerId = leftId
        self.draws = draws
        self.rightPlayerId = rightId
        self.rightWins = rWins
        self.note = note
    def __str__(self):
        return '<Bout(tourney=%s, results %s %d / %d / %s %d>'%(self.tourneyName,
                                                                self.lName, self.leftWins,
                                                                self.draws,
                                                                self.rName, self.rightWins)

###############################
## This bit fakes some data
#activePlayerNames = ['Andy', 'Bob', 'Carl', 'Donna', 'Erin', 'Fran']
#hiddenScores = { 'Andy':1.0, 'Bob':2.0, 'Carl':3.0, 'Donna': 4.0, 'Erin': 5.0, 'Fran':6.0}
#
#def genRandomBouts(activePlayerNames, nTrials):
#    result = []
#    for _ in xrange(nTrials):
#        pair = random.sample(activePlayerNames,2)
#        lP = session.query(LogitPlayer).filter_by(name=pair[0]).one()
#        rP = session.query(LogitPlayer).filter_by(name=pair[1]).one()
#        lWins = lP.fight(rP)
#        rWins = 1 - Wins
#        result.append( Bout(lWins,lP.id,rP.id,rWins,"random") )     
#    return resultd
#
#for name,score in hiddenScores.items():
#    thisPlayer = LogitPlayer(name,score,"")
#    session.add(thisPlayer)
#for i,b in enumerate(genRandomBouts(activePlayerNames,100)): 
#    session.add(b)
##############################

