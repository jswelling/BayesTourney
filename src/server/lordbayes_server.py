#! /usr/bin/env python

'''
Created on Jun 4, 2013

@author: welling
'''

import sys, os.path, time, json, math, random

from flask import render_template, session, send_from_directory, request
import numpy as np
import pandas as pd
from pathlib import Path
from pprint import pprint

import stat_utils
from database import db_session
from app import app
from models import Tourney, LogitPlayer, Bout

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

# @app.route('/converters/')
# @app.route('/converters/<path:urlpath>')
# def convertersexample(urlpath):
#     print('########## PONG!')
#     logMessage(f"test of {urlpath}")
#     try:
#         return render_template("converterexample.html", urlpath=urlpath)
#     except Exception as e:
#         return(str(e))  

# @app.route('/static/')
# @app.route('/static/<path:urlpath>')
# def server_static(urlpath):
#     print('######## PING!')
#     logMessage("static get of %s"%urlpath)
#     try:
#         return send_from_directory('../../www/static/', path)
#     except Exception as e:
#         logMessage("Static get failed: %s"%e)
#         raise e

#@app.route('/hello/:name')
#def index(name='World'):
#    return flask.template('<b>Hello {{name}}</b>!',name=name)

@app.route('/top')
def topPage():
#def topPage(db, uiSession):
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
        return render_template("entrants.tpl")
    elif path=='bouts':
        uiSession['curTab'] = 2
        #uiSession.changed()
        return render_template("bouts.tpl")
    elif path=='horserace':
        uiSession['curTab'] = 3
        #uiSession.changed()
        return render_template("horserace.tpl", db=db, Tourney=Tourney)
    elif path=='misc':
        uiSession['curTab'] = 4
        #uiSession.changed()
        return render_template("misc.tpl", db=db, Tourney=Tourney)
    elif path=='help':
        uiSession['curTab'] = 5
        #uiSession.changed()
        return render_template("info.tpl")
    else:
        raise RuntimeError("Unknown path /ajax/%s"%path)

def _orderAndChopPage(pList,fieldMap):
    sortIndex = request.args['sidx']
    sortOrder = request.args['sord']
    thisPageNum = int(request.args['page'])
    rowsPerPage = int(request.args['rows'])
    if sortIndex in fieldMap:
        field = fieldMap[sortIndex]
        pDict = {(getattr(p, field), idx) : p for idx, p in enumerate(pList)}
        sortMe = [tpl for tpl in pDict]
        print(f'field: {field}')
        pprint(sortMe)
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
def handleList(db, uiSession, path):
    logMessage("Request for /list/%s"%path)
    paramList = ['%s:%s'%(str(k),str(v)) for k,v in list(request.args.items())]
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
        raise RuntimeError("Bad path /list/%s"%path)
    
@app.route('/edit/<path>', methods=['POST'])
def handleEdit(path):
    db = db_session
    uiSession = session
    logMessage("Request for /edit/%s"%path)
    pprint(request.args)
    paramList = ['%s:%s'%(str(k),str(v)) for k,v in list(request.args.items())]
    logMessage("param list: %s"%paramList)
    if path=='edit_tourneys.json':
        if request.args['oper']=='edit':
            t = db.query(Tourney).filter_by(tourneyId=int(request.args['id'])).one()
            if 'name' in request.args:
                t.name = request.args['name']
            if 'notes' in request.args:
                t.note = request.args['notes']
            db.commit()
            return {}
        elif request.args['oper']=='add':
            name = request.args['name']
            notes = request.args['notes']
            if db.query(Tourney).filter_by(name=name).count() != 0:
                raise RuntimeError('There is already a tourney named %s'%name)
            t = Tourney(name,notes)
            db.add(t)
            db.commit()
            logMessage("Just added %s"%t)
            return {}
    elif path=='edit_bouts.json':
        if request.args['oper']=='edit':
            b = db.query(Bout).filter_by(boutId=int(request.args['id'])).one()
            if 'tourney' in request.args:
                b.tourneyId = int(request.args['tourney'])
            if 'rightplayer' in request.args:
                b.rightPlayerId = int(request.args['rightplayer'])
            if 'leftplayer' in request.args:
                b.leftPlayerId = int(request.args['leftplayer'])
            if 'rwins' in request.args:
                b.rWins = int(request.args['rwins'])
            if 'lwins' in request.args:
                b.lWins = int(request.args['lwins'])
            if 'draws' in request.args:
                b.draws = int(request.args['draws'])
            if 'notes' in request.args:
                b.note = request.args['notes']
            db.commit()
            return {}
        elif request.args['oper']=='add':
            tourneyId = int(request.args['tourney'])
            lPlayerId = int(request.args['leftplayer'])
            rPlayerId = int(request.args['rightplayer'])
            lWins = int(request.args['lwins'])
            rWins = int(request.args['rwins'])
            draws = int(request.args['draws'])
            note = request.args['notes']
            b = Bout(tourneyId,lWins,lPlayerId,rPlayerId,rWins,note)
            db.add(b)
            db.commit()
            logMessage("Just added %s"%b)
            return {}
        elif request.args['oper']=='del':
            b = db.query(Bout).filter_by(boutId=int(request.args['id'])).one()
            logMessage("Deleting %s"%b)
            db.delete(b)
            db.commit()
            return {}
    elif path=='edit_entrants.json':
        if request.args['oper']=='edit':
            p = db.query(LogitPlayer).filter_by(id=int(request.args['id'])).one()
            if 'name' in request.args:
                p.name = request.args['name']
            if 'notes' in request.args:
                p.note = request.args['notes']
            db.commit()
            return {}
        elif request.args['oper']=='add':
            name = request.args['name']
            notes = request.args['notes']
            if db.query(LogitPlayer).filter_by(name=name).count() != 0:
                raise RuntimeError('There is already an entrant named %s'%name)
            p = LogitPlayer(name,-1.0,notes)
            db.add(p)
            db.commit()
            logMessage("Just added %s"%p)
            return {}
    else:
        raise RuntimeError("Bad path /edit/%s"%path)

@app.route('/ajax/misc_download')
def handleDownloadReq(**kwargs):
    db = db_session
    uiSession = session
    with open(os.path.join(sessionScratchDir, 'downloadme.txt'), 'w') as f:
        f.write('hello world!\n')
    return flask.static_file('downloadme.txt', root=sessionScratchDir, download=True)

@app.route('/json/<path>')
def handleJSON(path, **kwargs):
    db = db_session
    uiSession = session
    print(f'kwargs: {kwargs}')
    print('db: ', db)
    print('uiSession: ', uiSession)
    print('session dict: %s' % repr(uiSession))
    logMessage("Request for /json/%s"%path)
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
        playerList = db.query(LogitPlayer)
        nPages,thisPageNum,totRecs,pList = _orderAndChopPage([p for p in playerList],
                                                             {'id':'id', 'name':'name', 'notes':'note'})
        result = {
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"id":p.id, "cell":[p.id, p.name, p.note]} for p in pList ]
                  }
    elif path =='bouts.json':
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
    elif path == 'horserace.json':
        paramList = ['%s:%s'%(str(k),str(v)) for k,v in list(request.args.items())]
        playerList = db.query(LogitPlayer)
        playerList = [(p.id, p) for p in playerList]
        playerList.sort()
        playerList = [p for _,p in playerList]
        print('playerList follows')
        print(playerList)
        tourneyId = int(request.args['tourney'])
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
            fitInfo = lordbayes_interactive.estimate(playerList,boutList)
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

#@app.route('/test')
#def test():
#    s = request.environ['beaker.session']
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
# application= SessionMiddleware(flask.app(), sessionOpts)



