#! /usr/bin/env python

'''
Created on Jun 4, 2013

@author: welling
'''

import sys, os.path, time, json, math, random

from flask import (render_template, session, send_from_directory,
                   request, send_file)
import numpy as np
import pandas as pd
from pathlib import Path
from pprint import pprint

import stat_utils
from database import db_session, engine
from app import app
from models import Tourney, LogitPlayer, Bout
import stat_utils

logFileName = '/tmp/tourneyserver.log'
sessionScratchDir = '/tmp'

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


def logMessage(txt):
    try:
        with open(logFileName,'a+') as f:
            f.write("%s %s\n"%(time.strftime('%Y/%m/%d %H:%M:%S'),txt))
    except Exception as e:
        print('exception %s on %s'%(e,txt))
        pass

@app.route('/top')
def topPage():
    return render_template("top.tpl", curTab=(session.get('curTab', None)))

@app.route('/notimpl')
def notimplPage():
    logMessage("request for unimplemented page")
    return flask.static_file('notimpl.html', root='../../www/static/')

@app.route('/ajax/<path>')
def handleAjax(path):
    uiSession = session
    db = db_session
    logMessage("Request for /ajax/%s"%path)
    if path=='tourneys':
        uiSession['curTab'] = 0
        pprint(uiSession)
        #uiSession.changed()
        return render_template("tourneys.tpl")
    elif path=='entrants':
        uiSession['curTab'] = 1
        #uiSession.changed()
        tourneyDict = {t.tourneyId: t.name for t in db.query(Tourney)}
        return render_template("entrants.tpl",
                               tourneyDict=tourneyDict)
    elif path=='bouts':
        uiSession['curTab'] = 2
        #uiSession.changed()
        tourneyDict = {t.tourneyId: t.name for t in db.query(Tourney)}
        return render_template("bouts.tpl",
                               tourneyDict=tourneyDict)
    elif path=='horserace':
        uiSession['curTab'] = 3
        #uiSession.changed()
        tourneyDict = {t.tourneyId: t.name for t in db.query(Tourney)}
        return render_template("horserace.tpl",
                               tourneyDict=tourneyDict)
    elif path=='misc':
        uiSession['curTab'] = 4
        #uiSession.changed()
        tourneyDict = {t.tourneyId: t.name for t in db.query(Tourney)}
        return render_template("misc.tpl",
                               tourneyDict=tourneyDict)
    elif path=='help':
        uiSession['curTab'] = 5
        #uiSession.changed()
        return render_template("info.tpl")
    else:
        raise RuntimeError("Unknown path /ajax/%s"%path)

def _orderAndChopPage(pList,fieldMap):
    sortIndex = request.values['sidx']
    sortOrder = request.values['sord']
    thisPageNum = int(request.values['page'])
    rowsPerPage = int(request.values['rows'])
    if sortIndex in fieldMap:
        field = fieldMap[sortIndex]
        pDict = {(getattr(p, field), idx) : p for idx, p in enumerate(pList)}
        sortMe = [tpl for tpl in pDict]
        if sortOrder == 'asc':
            sortMe.sort()
        else:
            sortMe.sort(reverse=True)
        pList = [pDict[tpl] for tpl in sortMe]
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
        raise RuntimeError("Sort index %s not in field map"%sortIndex)

@app.route('/list/<path>')
def handleList(path):
    db = db_session
    uiSession = session
    logMessage("Request for /list/%s"%path)
    paramList = ['%s:%s'%(str(k),str(v))
                 for k,v in list(request.values.items())]
    logMessage("param list: %s"%paramList)
    if path=='select_entrant':
        playerList = db.query(LogitPlayer)
        pairs = [(p.id,p.name) for p in playerList]
        pairs.sort()
        s = "<select>\n"
        for thisId,name in pairs:
            s += "<option value=%d>%s<option>\n"%(thisId,name)
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
        raise RuntimeError("Bad path /list/%s"%path)
    
@app.route('/edit/<path>', methods=['POST'])
def handleEdit(path):
    db = db_session
    uiSession = session
    logMessage("Request for /edit/%s"%path)
    pprint(request.values)
    paramList = ['%s:%s'%(str(k),str(v)) for k,v in list(request.values.items())]
    logMessage("param list: %s"%paramList)
    if path=='edit_tourneys.json':
        if request.values['oper']=='edit':
            t = db.query(Tourney).filter_by(tourneyId=int(request.values['id'])).one()
            if 'name' in request.values:
                t.name = request.values['name']
            if 'notes' in request.values:
                t.note = request.values['notes']
            db.commit()
            return {}
        elif request.values['oper']=='add':
            name = request.values['name']
            notes = request.values['notes']
            if db.query(Tourney).filter_by(name=name).count() != 0:
                raise RuntimeError('There is already a tourney named %s'%name)
            t = Tourney(name,notes)
            db.add(t)
            db.commit()
            logMessage("Just added %s"%t)
            return {}
    elif path=='edit_bouts.json':
        if request.values['oper']=='edit':
            b = db.query(Bout).filter_by(boutId=int(request.values['id'])).one()
            if 'tourney' in request.values:
                b.tourneyId = int(request.values['tourney'])
            if 'rightplayer' in request.values:
                b.rightPlayerId = int(request.values['rightplayer'])
            if 'leftplayer' in request.values:
                b.leftPlayerId = int(request.values['leftplayer'])
            if 'rwins' in request.values:
                b.rWins = int(request.values['rwins'])
            if 'lwins' in request.values:
                b.lWins = int(request.values['lwins'])
            if 'draws' in request.values:
                b.draws = int(request.values['draws'])
            if 'notes' in request.values:
                b.note = request.values['notes']
            db.commit()
            return {}
        elif request.values['oper']=='add':
            tourneyId = int(request.values['tourney'])
            lPlayerId = int(request.values['leftplayer'])
            rPlayerId = int(request.values['rightplayer'])
            lWins = int(request.values['lwins'])
            rWins = int(request.values['rwins'])
            draws = int(request.values['draws'])
            note = request.values['notes']
            b = Bout(tourneyId,lWins,lPlayerId,draws,rPlayerId,rWins,note)
            db.add(b)
            db.commit()
            logMessage("Just added %s"%b)
            return {}
        elif request.values['oper']=='del':
            b = db.query(Bout).filter_by(boutId=int(request.values['id'])).one()
            logMessage("Deleting %s"%b)
            db.delete(b)
            db.commit()
            return {}
    elif path=='edit_entrants.json':
        if request.values['oper']=='edit':
            p = db.query(LogitPlayer).filter_by(id=int(request.values['id'])).one()
            if 'name' in request.values:
                p.name = request.values['name']
            if 'notes' in request.values:
                p.note = request.values['notes']
            db.commit()
            return {}
        elif request.values['oper']=='add':
            name = request.values['name']
            notes = request.values['notes']
            if db.query(LogitPlayer).filter_by(name=name).count() != 0:
                raise RuntimeError('There is already an entrant named %s'%name)
            p = LogitPlayer(name,-1.0,notes)
            db.add(p)
            db.commit()
            logMessage("Just added %s"%p)
            return {}
    else:
        raise RuntimeError("Bad path /edit/%s"%path)

@app.route('/ajax/bouts_download')
def handleDownloadReq(**kwargs):
    db = db_session
    uiSession = session

    paramList = ['%s:%s'%(str(k),str(v)) for k,v in list(request.values.items())]
    tourneyId = int(request.values.get('tourney', '-1'))

    if tourneyId >= 0:
        boutDF = pd.read_sql(f'select * from bouts where tourneyId={tourneyId}',
                             engine, coerce_float=True)
    else:
        boutDF = pd.read_sql_table('bouts', engine, coerce_float=True)
    print(boutDF.columns)
    print(boutDF)
    
    full_path =  Path(sessionScratchDir) / 'bouts.tsv'
    boutDF.to_csv(full_path, sep='\t', index=False)
    logMessage(f"Download bouts requested; generated and sent sending {full_path}")
    return send_file(full_path,
                     as_attachment=True,
    )

@app.route('/ajax/entrants_download')
def handleEntrantsDownloadReq(**kwargs):
    db = db_session
    uiSession = session

    paramList = ['%s:%s'%(str(k),str(v)) for k,v in list(request.values.items())]
    tourneyId = int(request.values.get('tourney', '-1'))

    if tourneyId >= 0:
        entrantDF = pd.read_sql('select distinct players.*'
                                'from players inner join bouts'
                                ' on ( bouts.leftPlayerId = players.id or bouts.rightPlayerId = players.id )'
                                f' where bouts.tourneyId={tourneyId}',
                                engine, coerce_float=True)
    else:
        entrantDF = pd.read_sql_table('players', engine, coerce_float=True)
    
    full_path =  Path(sessionScratchDir) / 'entrants.tsv'
    entrantDF.to_csv(full_path, sep='\t', index=False)
    logMessage(f"Download entrants requested; generated and sent sending {full_path}")
    return send_file(full_path,
                     as_attachment=True,
    )

@app.route('/json/<path>')
def handleJSON(path, **kwargs):
    db = db_session
    uiSession = session
    print('session dict: %s' % repr(uiSession))
    logMessage("Request for /json/%s"%path)
    logMessage(f"params: {[(k,request.values[k]) for k in request.values]}")
    if path=='tourneys.json':
        tourneyList = db.query(Tourney)
        nPages,thisPageNum,totRecs,pList = _orderAndChopPage([t for t in tourneyList],
                                                             {'id':'tourneyId', 'name':'name', 'notes':'note'})
        result = {
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"id":t.tourneyId, "cell":[t.tourneyId, t.name, t.note]} 
                           for t in tourneyList ]
                  }
    elif path=='entrants.json':
        tourneyId = int(request.values.get('tourneyId', -1))
        if tourneyId >= 0:
            with engine.connect() as conn:
                rs = conn.execute('select distinct players.*'
                                  'from players inner join bouts'
                                  ' on ( bouts.leftPlayerId = players.id'
                                  ' or bouts.rightPlayerId = players.id )'
                                  f' where bouts.tourneyId={tourneyId}')
                playerList = [val for val in rs]
        else:
            playerList = [val for val in db.query(LogitPlayer)]
        nPages,thisPageNum,totRecs,pList = _orderAndChopPage([p for p in playerList],
                                                             {'id':'id', 'name':'name',
                                                              'notes':'note'})
        result = {
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"id":p.id, "cell":[p.id, p.name, p.note]} for p in pList ]
                  }
    elif path =='bouts.json':
        tourneyId = int(request.values.get('tourneyId', -1))
        if tourneyId >= 0:
            boutList = [b for b in db.query(Bout).filter_by(tourneyId=tourneyId)]
        else:
            boutList = [b for b in db.query(Bout)]
        nPages,thisPageNum,totRecs,boutList = _orderAndChopPage(boutList,
                                                                {'tourney':'tourneyId',
                                                                 'lwins':'leftWins', 
                                                                 'rwins':'rightWins',
                                                                 'leftplayer':'lName',
                                                                 'rightplayer':'rName',
                                                                 'draws':'draws',
                                                                 'notes':'note'})
        result = {
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"id":p.boutId, "cell":[p.tourneyName, 
                                                    p.leftWins, p.lName, p.draws, p.rName, p.rightWins, p.note] } 
                           for p in boutList ]
                  }
        logMessage("returning %s"%result)
    elif path == 'horserace_go.json':
        paramList = ['%s:%s'%(str(k),str(v)) for k,v in list(request.values.items())]
        logMessage(f"horserace_go! {paramList}")
        result = {}
    elif path == 'horserace.json':
        paramList = ['%s:%s'%(str(k),str(v)) for k,v in list(request.values.items())]
        playerList = db.query(LogitPlayer)
        playerList = [(p.id, p) for p in playerList]
        playerList.sort()
        playerList = [p for _,p in playerList]
        print('playerList follows')
        print(playerList)
        tourneyId = int(request.values['tourney'])
        boutList = db.query(Bout)
        boutDF = pd.read_sql_table('bouts', engine, coerce_float=False)
        print(boutDF)
        if tourneyId >= 0:
            boutList = boutList.filter_by(tourneyId=tourneyId)
            playerS = set([b.leftPlayerId for b in boutList] + [b.rightPlayerId for b in boutList])
            playerList = [p for p in playerList if p.id in playerS]
        print('boutList follows')
        print(boutList)
        print('trimmed playerList follows')
        print(playerList)
        try:
            fitInfo = stat_utils.estimate(playerList,boutList)
            for p,w in fitInfo: p.weight = w
            pList = [p for p,_ in fitInfo]
        except RuntimeError as e:
            logMessage('horseRace exception: %s' % str(e))
            for p in playerList:
                p.weight = np.nan
                pList = [p for p in playerList]
        nPages,thisPageNum,totRecs,pList = _orderAndChopPage(pList,
                                                             {'id':'id', 'name':'name', 'notes':'note',
                                                              'estimate':'weight', 'bearpit':'bearpit'})
        result = {
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"id":p.id, "cell":[p.id, p.name, 0, str(p.weight), p.note]} 
                           for i,p in enumerate(pList) ]
                  }
    else:
        raise RuntimeError("Request for unknown AJAX element %s"%path)
    return result




