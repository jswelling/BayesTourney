#! /usr/bin/env python

'''
Created on Jun 4, 2013

@author: welling
'''

import sys, os.path, time, json, math, random

import bottle
import numpy as np
import pandas as pd
#import bottle_sqlite

#from beaker.middleware import SessionMiddleware
#from bottle_sqlalchemy import Plugin as SQLAlchemyPlugin
import session_support
#from bottle_beaker import BeakerPlugin

import lordbayes_interactive

#sqlite = bottle_sqlite.SQLitePlugin(dbfile='/tmp/test.db')
#bottle.install(sqlite)

logFileName = '/tmp/tourneyserver.log'
sessionScratchDir = '/tmp'
dbURI = 'sqlite:///../../data/mydb.db'

from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey
from sqlalchemy import select, func
engine= create_engine(dbURI, echo=True)
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from sqlalchemy.orm import sessionmaker, column_property

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

Base.metadata.create_all(engine)

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
#        rWins = 1 - lWins
#        result.append( Bout(lWins,lP.id,rP.id,rWins,"random") )     
#    return result
#
#for name,score in hiddenScores.items():
#    thisPlayer = LogitPlayer(name,score,"")
#    session.add(thisPlayer)
#for i,b in enumerate(genRandomBouts(activePlayerNames,100)): 
#    session.add(b)
##############################


def logMessage(txt):
    try:
        with open(logFileName,'a+') as f:
            f.write("%s %s\n"%(time.strftime('%Y/%m/%d %H:%M:%S'),txt))
    except Exception,e:
        print 'exception %s on %s'%(e,txt)
        pass

@bottle.route('/static/<filepath:path>')
def server_static(filepath):
    logMessage("static get of %s"%filepath)
    try:
        return bottle.static_file(filepath, root='../../www/static/')
    except Exception,e:
        logMessage("Static get failed: %s"%e)
        raise e

#@bottle.route('/hello/:name')
#def index(name='World'):
#    return bottle.template('<b>Hello {{name}}</b>!',name=name)

@bottle.route('/top')
def topPage():
    return bottle.template("top.tpl")

@bottle.route('/notimpl')
def notimplPage():
    logMessage("request for unimplemented page")
    return bottle.static_file('notimpl.html', root='../../www/static/')

@bottle.route('/ajax/<path>')
def handleAjax(db, uiSession, path):
    logMessage("Request for /ajax/%s"%path)
    if path=='tourneys':
        return bottle.template("tourneys.tpl")
    elif path=='entrants':
        return bottle.template("entrants.tpl")
    elif path=='bouts':
        return bottle.template("bouts.tpl")
    elif path=='horserace':
        return bottle.template("horserace.tpl", db=db, Tourney=Tourney)
    elif path=='help':
        return bottle.template("info.tpl")
    else:
        raise bottle.BottleException("Unknown path /ajax/%s"%path)

def _orderAndChopPage(pList,fieldMap,bottleRequest):
    sortIndex = bottleRequest.params['sidx']
    sortOrder = bottleRequest.params['sord']
    thisPageNum = int(bottleRequest.params['page'])
    rowsPerPage = int(bottleRequest.params['rows'])
    if sortIndex in fieldMap:
        field = fieldMap[sortIndex]
        pList = [(getattr(p,field),p) for p in pList]
        if sortOrder == 'asc':
            pList.sort()
        else:
            pList.sort(reverse=True)
        pList = [p for _,p in pList]
        nPages = int(math.ceil(float(len(pList))/(rowsPerPage-1)))
        totRecs = len(pList)
        if thisPageNum == nPages:
            eR = totRecs
            sR = max(eR - rowsPerPage, 0)
        else:
            sR = (thisPageNum-1)*(rowsPerPage-1)
            eR = sR + rowsPerPage
        pList = pList[sR:eR]
        return (nPages,thisPageNum,totRecs,pList)
    else:
        raise bottle.BottleException("Sort index %s not in field map"%sortIndex)

@bottle.route('/list/<path>')
def handleList(db, uiSession, path):
    logMessage("Request for /list/%s"%path)
    paramList = ['%s:%s'%(str(k),str(v)) for k,v in bottle.request.params.items()]
    logMessage("param list: %s"%paramList)
    if path=='select_entrant':
        playerList = db.query(LogitPlayer)
        pairs = [(p.id,p.name) for p in playerList]
        pairs.sort()
        s = "<select>\n"
        for thisId,name in pairs: s += "<option value=%d>%s<option>\n"%(thisId,name)
        s += "</select>\n"
        return s
    elif path=='select_tourney':
        tourneyList = db.query(Tourney)
        pairs = [((t.tourneyId,t.name)) for t in tourneyList]
        pairs.sort()
        s = "<select>\n"
        for thisId,name in pairs: s += "<option value=%d>%s<option>\n"%(thisId,name)
        s += "</select>\n"
        return s
    else:
        raise bottle.BottleException("Bad path /list/%s"%path)
    
@bottle.route('/edit/<path>', method='POST')
def handleEdit(db, uiSession, path):
    logMessage("Request for /edit/%s"%path)
    paramList = ['%s:%s'%(str(k),str(v)) for k,v in bottle.request.params.items()]
    logMessage("param list: %s"%paramList)
    if path=='edit_tourneys.json':
        if bottle.request.params['oper']=='edit':
            t = db.query(Tourney).filter_by(tourneyId=int(bottle.request.params['id'])).one()
            if 'name' in bottle.request.params:
                t.name = bottle.request.params['name']
            if 'notes' in bottle.request.params:
                t.note = bottle.request.params['notes']
            db.commit()
            return {}
        elif bottle.request.params['oper']=='add':
            name = bottle.request.params['name']
            notes = bottle.request.params['notes']
            if db.query(Tourney).filter_by(name=name).count() != 0:
                raise bottle.BottleException('There is already a tourney named %s'%name)
            t = Tourney(name,notes)
            db.add(t)
            db.commit()
            logMessage("Just added %s"%t)
            return {}
    elif path=='edit_bouts.json':
        if bottle.request.params['oper']=='edit':
            b = db.query(Bout).filter_by(boutId=int(bottle.request.params['id'])).one()
            if 'tourney' in bottle.request.params:
                b.tourneyId = int(bottle.request.params['tourney'])
            if 'rightplayer' in bottle.request.params:
                b.rightPlayerId = int(bottle.request.params['rightplayer'])
            if 'leftplayer' in bottle.request.params:
                b.leftPlayerId = int(bottle.request.params['leftplayer'])
            if 'rwins' in bottle.request.params:
                b.rWins = int(bottle.request.params['rwins'])
            if 'lwins' in bottle.request.params:
                b.lWins = int(bottle.request.params['lwins'])
            if 'draws' in bottle.request.params:
                b.draws = int(bottle.request.params['draws'])
            if 'notes' in bottle.request.params:
                b.note = bottle.request.params['notes']
            db.commit()
            return {}
        elif bottle.request.params['oper']=='add':
            tourneyId = int(bottle.request.params['tourney'])
            lPlayerId = int(bottle.request.params['leftplayer'])
            rPlayerId = int(bottle.request.params['rightplayer'])
            lWins = int(bottle.request.params['lwins'])
            rWins = int(bottle.request.params['rwins'])
            draws = int(bottle.request.params['draws'])
            note = bottle.request.params['notes']
            b = Bout(tourneyId,lWins,lPlayerId,rPlayerId,rWins,note)
            db.add(b)
            db.commit()
            logMessage("Just added %s"%b)
            return {}
        elif bottle.request.params['oper']=='del':
            b = db.query(Bout).filter_by(boutId=int(bottle.request.params['id'])).one()
            logMessage("Deleting %s"%b)
            db.delete(b)
            db.commit()
            return {}
    elif path=='edit_entrants.json':
        if bottle.request.params['oper']=='edit':
            p = db.query(LogitPlayer).filter_by(id=int(bottle.request.params['id'])).one()
            if 'name' in bottle.request.params:
                p.name = bottle.request.params['name']
            if 'notes' in bottle.request.params:
                p.note = bottle.request.params['notes']
            db.commit()
            return {}
        elif bottle.request.params['oper']=='add':
            name = bottle.request.params['name']
            notes = bottle.request.params['notes']
            if db.query(LogitPlayer).filter_by(name=name).count() != 0:
                raise bottle.BottleException('There is already an entrant named %s'%name)
            p = LogitPlayer(name,-1.0,notes)
            db.add(p)
            db.commit()
            logMessage("Just added %s"%p)
            return {}
    else:
        raise bottle.BottleException("Bad path /edit/%s"%path)

@bottle.route('/json/<path>')
def handleJSON(db, uiSession, path, **kwargs):
    print 'kwargs were %s' % kwargs
    print 'db: ', db
    print 'uiSession: ', uiSession
    print 'session dict: %s' % repr(uiSession)
    logMessage("Request for /json/%s"%path)
    if path=='tourneys.json':
        tourneyList = db.query(Tourney)
        nPages,thisPageNum,totRecs,pList = _orderAndChopPage([t for t in tourneyList],
                                                             {'id':'tourneyId', 'name':'name', 'notes':'note'},
                                                             bottle.request)
        result = {
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"id":t.tourneyId, "cell":[t.tourneyId, t.name, t.note]} 
                           for t in tourneyList ]
                  }
    elif path=='entrants.json':
        playerList = db.query(LogitPlayer)
        nPages,thisPageNum,totRecs,pList = _orderAndChopPage([p for p in playerList],
                                                             {'id':'id', 'name':'name', 'notes':'note'},
                                                             bottle.request)
        result = {
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"id":p.id, "cell":[p.id, p.name, p.note]} for p in pList ]
                  }
        uiSession['hello'] = 'world'
    elif path =='bouts.json':
        boutList = [b for b in db.query(Bout)]
        nPages,thisPageNum,totRecs,boutList = _orderAndChopPage(boutList,
                                                                {'tourney':'tourneyId',
                                                                 'lwins':'leftWins', 
                                                                 'rwins':'rightWins',
                                                                 'leftplayer':'lName',
                                                                 'rightplayer':'rName',
                                                                 'draws':'draws',
                                                                 'notes':'note'},
                                                                bottle.request)
        result = {
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"id":p.boutId, "cell":[p.tourneyName, 
                                                    p.leftWins, p.lName, p.draws, p.rName, p.rightWins, p.note] } 
                           for p in boutList ]
                  }
        logMessage("returning %s"%result)
    elif path == 'horserace.json':
        paramList = ['%s:%s'%(str(k),str(v)) for k,v in bottle.request.params.items()]
        playerList = db.query(LogitPlayer)
        playerList = [(p.id, p) for p in playerList]
        playerList.sort()
        playerList = [p for _,p in playerList]
        print 'playerList follows'
        print playerList
        tourneyId = int(bottle.request.params['tourney'])
        boutList = db.query(Bout)
        boutDF = pd.read_sql_table('bouts', engine, coerce_float=False)
        print boutDF
        if tourneyId >= 0:
            boutList = boutList.filter_by(tourneyId=tourneyId)
            playerS = set([b.leftPlayerId for b in boutList] + [b.rightPlayerId for b in boutList])
            playerList = [p for p in playerList if p.id in playerS]
        print 'boutList follows'
        print boutList
        print 'trimmed playerList follows'
        print playerList
        try:
            fitInfo = lordbayes_interactive.estimate(playerList,boutList)
            for p,w in fitInfo: p.weight = w
            pList = [p for p,_ in fitInfo]
        except bottle.BottleException as e:
            logMessage('horseRace exception: %s' % str(e))
            for p in playerList:
                p.weight = np.nan
                pList = [p for p in playerList]
        nPages,thisPageNum,totRecs,pList = _orderAndChopPage(pList,
                                                             {'id':'id', 'name':'name', 'notes':'note',
                                                              'estimate':'weight', 'bearpit':'bearpit'},
                                                             bottle.request)
        result = {
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"id":p.id, "cell":[p.id, p.name, 0, str(p.weight), p.note]} 
                           for i,p in enumerate(pList) ]
                  }
    else:
        raise bottle.BottleException("Request for unknown AJAX element %s"%path)
    return result

#@bottle.route('/test')
#def test():
#    s = bottle.request.environ['beaker.session']
#    if 'test' in s:
#        s['test'] += 1
#    else:
#        s['test'] = 1
#    s.save()
#    return 'Test counter: %d' % s['test']

# sessionOpts = {
#                'session.type':'ext:database',
#                'session.url':'sqlite:///%s/%s.db'%(sessionScratchDir,'tourney'),
#                'session.lock_dir':'/tmp'
#                }
# 
# sessionOpts = { 'session.cookie_expires':True}
# application= SessionMiddleware(bottle.app(), sessionOpts)

application = session_support.wrapBottleApp(bottle.app(), engine, sessionmaker(bind=engine))


