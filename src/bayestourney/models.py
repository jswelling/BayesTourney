from datetime import datetime

from sqlalchemy import (Column, Integer, Float, String, ForeignKey, JSON,
                        DateTime, Boolean)
from sqlalchemy import select
from sqlalchemy.orm import Query, column_property

from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash

from .database import Base

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
        db.add(UserGroupPair(self.id, group.id))

    def remove_group(self, db, group):
        (db.query(UserGroupPair)
         .filter(UserGroupPair.user_id == self.id)
         .filter(UserGroupPair.group_id == group.id)
         .delete())


class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return(f'<Group({self.id}, name={self.name})>')


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
    ownerName = column_property(select([User.username]).where(User.id==owner)
                                .scalar_subquery())
    groupName = column_property(select([Group.name]).where(Group.id==group)
                                .scalar_subquery())
    
    def __init__(self, name, owner, group, note=''):
        self.name = name
        self.owner = owner
        self.group = group
        self.note = note
        
    def __str__(self):
        return "<Tourney(%s) owned by %s, group %s>"%(self.name,
                                                      self.ownerName, self.groupName)

class LogitPlayer(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    note = Column(String)
    
    def __init__(self,name,note):
        self.name = name
        self.note = note
    def __str__(self): return self.name
    def fight(self,otherPlayer):
        raise RuntimeError('since LogitPlayer no longer has a weight, fight is no longer implemented')
        
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

