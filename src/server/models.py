from database import Base

from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy import select
from sqlalchemy.orm import column_property

class Tourney(Base):
    __tablename__ = 'tourneys'
    tourneyId = Column(Integer, primary_key=True)
    name = Column(String)
    note = Column(String)
    
    def __init__(self,name,note=''):
        self.name = name
        self.note = note
        
    def __str__(self):
        return "<Tourney(%s)>"%self.name

class LogitPlayer(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    weight = Column(Float)
    note = Column(String)
    
    def __init__(self,name,weight,note):
        self.name = name
        self.weight = weight
        self.note = note
    def __str__(self): return self.name
    def fight(self,otherPlayer):
        assert isinstance(otherPlayer,LogitPlayer), "%s can only fight LogitPlayers"%self.name
        if random.random() < self.weight/(self.weight+otherPlayer.weight): return 0
        else: return 1
        
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
    lName = column_property(select([LogitPlayer.name]).where(LogitPlayer.id==leftPlayerId))
    rName = column_property(select([LogitPlayer.name]).where(LogitPlayer.id==rightPlayerId))
    tourneyName = column_property(select([Tourney.name]).where(Tourney.tourneyId==tourneyId))
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

