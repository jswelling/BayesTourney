#! /usr/bin/env python

'''
Created on Jun 4, 2013

@author: welling
'''

import base64
import io
import time
import json
import logging
import functools
from math import ceil

from flask import (
    Blueprint, flash, g, render_template, request, url_for,
    send_from_directory, send_file, session, redirect, current_app
)
from werkzeug.utils import secure_filename
from werkzeug.routing import BuildError
from werkzeug.exceptions import abort
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from pathlib import Path
from pprint import pprint

from .database import get_db
from .auth import login_required
from .models import Tourney, LogitPlayer, Bout
from .settings import get_settings, set_settings, SettingsError
from . import stat_utils


UPLOAD_ALLOWED_EXTENSIONS = ['tsv', 'csv']


logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

bp = Blueprint('', __name__)


def logMessage(txt):
    LOGGER.info(txt)


def debug_wrapper(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        LOGGER.debug(f'{request.method} Request for {request.endpoint}'
                     f' kwargs {kwargs}'
                     f' params {[(k,request.values[k]) for k in request.values]}')
        rslt = view(**kwargs)
        LOGGER.debug(f'Returning {rslt}')
        return rslt
    return wrapped_view

    
def debug_page_wrapper(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        LOGGER.debug(f'{request.method} Request for {request.endpoint}'
                     f' kwargs {kwargs}'
                     f' params {[(k,request.values[k]) for k in request.values]}'
        )
        rslt = view(**kwargs)
        return rslt
    return wrapped_view

    
def allowed_upload_file(filename):
    return ('.' in filename and
            Path(filename).suffix[1:] in UPLOAD_ALLOWED_EXTENSIONS)


@bp.route("/upload/entrants", methods=['POST'])
def upload_entrants_file():
    """
    This is an AJAX transaction
    """
    # check of the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        LOGGER.info('upload with no file part')
        return "No file provided", 400
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        LOGGER.info('upload with empty file part')
        return "request had an empty file", 400
    if not allowed_upload_file(file.filename):
        LOGGER.info('file type not supported for upload')
        return 'file type not supported for upload', 400
    filename = secure_filename(file.filename)
    LOGGER.info(f'Saving file to {filename}')
    file.save(Path(current_app.config['UPLOAD_FOLDER'])
              / filename)
    LOGGER.info('Save complete')
    return {"status":"success"}


class DBException(Exception):
    pass


def player_name_to_id(row, key, db):
    p_list = [p for p in db.query(LogitPlayer).filter_by(name=row[key])]
    if len(p_list) == 1:
        return p_list[0].id
    else:
        return -1  # we need to use an int as the signal value for Pandas' sake


def insert_bouts_from_df(df, tourney):
    col_set = set([str(col) for col in df.columns])
    db = get_db()
    if set(["leftWins", "leftPlayerName", "rightPlayerName",
            "rightWins", "draws"]).issubset(col_set):
        df["tourneyId"] = tourney.tourneyId
        df['leftPlayerId'] = df.apply(player_name_to_id,
                                       key='leftPlayerName',
                                       db=db,
                                       axis=1)
        df['rightPlayerId'] = df.apply(player_name_to_id,
                                       key='rightPlayerName',
                                       db=db,
                                       axis=1)
        bad_names = df[df['leftPlayerId'] == -1]['leftPlayerName']
        bad_names = bad_names.append(df[df['rightPlayerId'] == -1]['rightPlayerName'])
        if bad_name_l := [nm for nm in bad_names.unique()]:
            bad_name_str = ', '.join([f'"{nm}"' for nm in bad_name_l])
            raise DBException(f'Unknown or multiply defined player names: {bad_name_str}')
        else:
            df = df.drop(columns=['leftPlayerName', 'rightPlayerName', 'tourneyName'])
            print(df)
            for idx, row in df.iterrows():
                print(row)
                new_bout = Bout(int(row['tourneyId']),
                                int(row['leftWins']), int(row['leftPlayerId']),
                                int(row['draws']),
                                int(row['rightPlayerId']), int(row['rightWins']),
                                note = "just inserted this")
                db.add(new_bout)
                print(new_bout)
            db.commit()
                         
    else:
        raise DBException('Unknown column pattern for bouts')


@bp.route("/upload/bouts", methods=['POST'])
@debug_page_wrapper
def upload_bouts_file():
    """
    This is an AJAX transaction
    """
    # check of the post request has the file part
    if 'file' not in request.files:
        LOGGER.info(msg := 'no file part')
        return msg, 400
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        LOGGER.info(msg := 'upload with empty file part')
        return msg, 400
    if not allowed_upload_file(file.filename):
        LOGGER.info(msg := 'file type not supported for upload')
        return msg, 400
    if 'tournament' in request.values:
        tourney_id_str = request.values['tournament']
    else:
        LOGGER.info(msg := 'bout upload tournament id is missing')
        return msg, 400
    try:
        tourney_id = int(tourney_id_str)
    except ValueError:
        LOGGER.info(msg := 'bout upload tournament id invalid format')
        return msg, 400
    if tourney_id < 0:
        LOGGER.info(msg := 'bout upload tournament id is not valid')
        return msg, 400
    filename = secure_filename(file.filename)
    LOGGER.info(f'Saving file to {filename}')
    file_fullpath = Path(current_app.config['UPLOAD_FOLDER']) / filename
    file.save(file_fullpath)
    LOGGER.info('Save complete')
    if filename.endswith('.tsv'):
        df = pd.read_csv(file_fullpath, sep='\t')
    else:
        df = pd.read_csv(file_fullpath)
    LOGGER.info('Parse complete')
    tourney = get_db().query(Tourney).filter_by(tourneyId=tourney_id).one()
    LOGGER.info(f'Tourney is {tourney}')
    try:
        insert_bouts_from_df(df, tourney)
    except DBException as e:
        LOGGER.info(f'DBException: {e}')
        return {"status":"failure", "msg":str(e)}
    file_fullpath.unlink()
    LOGGER.info('Uploaded file was unlinked')
    return {"status":"success"}


@bp.route("/site-map")
def site_map():
    links = []
    for rule in current_app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods or 'POST' in rule.methods:
            try:
                url = url_for(rule.endpoint, **(rule.defaults or {}))
            except BuildError as e:
                url = f'BuildError {e}'
            links.append((url, rule.endpoint))
    # links is now a list of url, endpoint tuples
    return render_template("site_map.html",
                           link_dict={k:v for k, v in links})
    print(links)


@bp.route("/settings")
def settings():
    return render_template("prefs.html", **(get_settings()))


@bp.route('/')
@login_required
def index():
    return redirect(url_for('tourneys'))


@bp.route('/tourneys')
@login_required
@debug_page_wrapper
def tourneys():
    return render_template("tourneys.tpl")


@bp.route('/entrants')
@login_required
@debug_page_wrapper
def entrants():
    tourneyDict = {t.tourneyId: t.name for t in get_db().query(Tourney)}
    return render_template("entrants.tpl",
                           tourneyDict=tourneyDict)


@bp.route('/bouts')
@login_required
@debug_page_wrapper
def bouts():
    tourneyDict = {t.tourneyId: t.name for t in get_db().query(Tourney)}
    return render_template("bouts.tpl",
                           tourneyDict=tourneyDict)


@bp.route('/experiment')
#login_required
def experiment():
    g.user.prefs = None
    get_db().commit()


@bp.route('/horserace')
@login_required
@debug_page_wrapper
def horserace():
    tourneyDict = {t.tourneyId: t.name for t in get_db().query(Tourney)}
    return render_template("horserace.tpl",
                           tourneyDict=tourneyDict)

@bp.route('/help')
@debug_page_wrapper
def help():
    return render_template("info.tpl")    


@bp.route('/notimpl')
@debug_page_wrapper
def notimplPage():
    return flask.static_file('notimpl.html', root='../../www/static/')


def _orderAndChopPage(pList,fieldMap):
    """
    This was very useful for the old version of jqGrid, before 'loadonce: true'
    """
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
        nPages = int(ceil(float(len(pList))/(rowsPerPage-1)))
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

@bp.route('/list/<path>')
@debug_page_wrapper
def handleList(path):
    """
    Used for populating select elements
    returns html
    """
    db = get_db()
    uiSession = session
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
    

@bp.route('/edit/<path>', methods=['POST'])
@debug_wrapper
def handleEdit(path):
    """
    Specialized endpoint that understands the requests jqgrid uses to perform edits
    """
    db = get_db()
    uiSession = session
    paramList = ['%s:%s'%(str(k),str(v)) for k,v in list(request.values.items())]
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
            return {}
        elif request.values['oper']=='del':
            tourneyId = int(request.values['id'])
            bouts = db.query(Bout).filter_by(tourneyId=tourneyId)
            for bout in bouts:
                db.delete(bout)
            tourney = db.query(Tourney).filter_by(tourneyId=tourneyId).one()
            db.delete(tourney)
            db.commit()
            return {}
        else:
            raise RuntimeError(f"Bad edit operation {request.values['oper']}")
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
            return {}
        elif request.values['oper']=='del':
            b = db.query(Bout).filter_by(boutId=int(request.values['id'])).one()
            db.delete(b)
            db.commit()
            return {}
        else:
            raise RuntimeError(f"Bad edit operation {request.values['oper']}")
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
            return {}
        elif request.values['oper'] == 'del':
            return "not implemented", 400
        else:
            raise RuntimeError(f"Bad edit operation {request.values['oper']}")
    else:
        raise RuntimeError("Bad path /edit/%s"%path)


@bp.route('/download/bouts')
@debug_page_wrapper
def handleBoutsDownloadReq(**kwargs):
    db = get_db()
    engine = db.get_bind()
    uiSession = session

    tourneyId = int(request.values.get('tourney', '-1'))

    if tourneyId >= 0:
        boutDF = pd.read_sql(
            f"""
            select tourneys.name as tourneyName, 
            bouts.leftWins as leftWins, lplayers.name as leftPlayerName, 
            rplayers.name as rightPlayerName, bouts.rightWins as rightWins, 
            bouts.draws as draws 
            from bouts, tourneys, players as lplayers, players as rplayers 
            where bouts.leftPlayerId = lplayers.id 
            and bouts.rightPlayerId = rplayers.id 
            and tourneys.tourneyId = bouts.tourneyId 
            and bouts.tourneyId = {tourneyId}
            """, engine, coerce_float=True)
    else:
        boutDF = pd.read_sql(
            """
            select tourneys.name as tourneyName, 
            bouts.leftWins as leftWins, lplayers.name as leftPlayerName, 
            rplayers.name as rightPlayerName, bouts.rightWins as rightWins, 
            bouts.draws as draws 
            from bouts, tourneys, players as lplayers, players as rplayers 
            where bouts.leftPlayerId = lplayers.id 
            and bouts.rightPlayerId = rplayers.id 
            and tourneys.tourneyId = bouts.tourneyId 
            """, engine, coerce_float=True)
    
    session_scratch_dir = current_app.config['SESSION_SCRATCH_DIR']
    full_path =  Path(session_scratch_dir) / 'bouts.tsv'
    boutDF.to_csv(full_path, sep='\t', index=False)
    return send_file(full_path, as_attachment=True)


@bp.route('/download/entrants')
@debug_page_wrapper
def handleEntrantsDownloadReq(**kwargs):
    db = get_db()
    engine = db.get_bind()
    uiSession = session

    tourneyId = int(request.values.get('tourney', '-1'))

    if tourneyId >= 0:
        entrantDF = pd.read_sql('select distinct players.*'
                                ' from players inner join bouts'
                                ' on ( bouts.leftPlayerId = players.id or bouts.rightPlayerId = players.id )'
                                f' where bouts.tourneyId={tourneyId}',
                                engine, coerce_float=True)
    else:
        entrantDF = pd.read_sql_table('players', engine, coerce_float=True)
    
    session_scratch_dir = current_app.config['SESSION_SCRATCH_DIR']
    full_path =  Path(session_scratch_dir) / 'entrants.tsv'
    entrantDF.to_csv(full_path, sep='\t', index=False)
    return send_file(full_path, as_attachment=True)


def _include_fun(row, keycols, checkbox_dict):
    flags = [checkbox_dict.get(row[keycol], False) for keycol in keycols]
    return all(flags)


@bp.route('/horserace_go', methods=['POST'])
@debug_page_wrapper
@login_required
def horserace_go(**kwargs):
    db = get_db()
    engine = db.get_bind()
    uiSession = session
    data = request.get_json()
    #logMessage(f"data: {data}")
    tourneyId = int(data['tourney'])
    if tourneyId >= 0:
        boutDF = pd.read_sql(f'select * from bouts'
                             f' where tourneyId={tourneyId}',
                             engine, coerce_float=True)
        playerDF = pd.read_sql('select distinct players.*'
                               ' from players inner join bouts'
                               ' on ( bouts.leftPlayerId = players.id'
                               ' or bouts.rightPlayerId = players.id )'
                               f' where bouts.tourneyId={tourneyId}',
                               engine, coerce_float=True)
    else:
        boutDF = pd.read_sql_table('bouts', engine, coerce_float=True)
        playerDF = pd.read_sql_table('players', engine, coerce_float=True)
    checkbox_dict = {int(k): v for k, v in data['checkboxes'].items()}
    playerDF = playerDF[playerDF.apply(_include_fun, axis=1,
                                       keycols=['id'], checkbox_dict=checkbox_dict)]
    boutDF = boutDF[boutDF.apply(_include_fun, axis=1,
                                 keycols=['leftPlayerId', 'rightPlayerId'],
                                 checkbox_dict=checkbox_dict)]
    output = io.BytesIO()
    
    try:
        fit_info = stat_utils.estimate(playerDF, boutDF)
        fig, axes = plt.subplots(ncols=1, nrows=1)
        graph_type_dct = {'hr_graph_style_box': 'boxplot',
                          'hr_graph_style_violin': 'violin'}
        graph_type = graph_type_dct[get_settings()['hr_graph_style']]
        fit_info.gen_graph(fig, axes, graph_type)
        FigureCanvas(fig).print_png(output)
        
    except RuntimeError as e:
        logMessage('horseRace_go exception: %s' % str(e))
    result = {'image': ('data:image/png;base64,'
                        + base64.b64encode(output.getvalue()).decode("ascii")),
              'announce_html': fit_info.estimate_win_probabilities().as_html()
              }

    return result
    

@bp.route('/ajax/settings', methods=["GET", "PUT"])
@login_required
@debug_page_wrapper
def ajax_settings(**kwargs):
    if request.method == 'GET':
        return {'status': 'success',
                'value': {k:v for k, v in get_settings().items()}
                }
    elif request.method == 'PUT':
        name = request.values['name']
        id = request.values['id']
        if name in get_settings():
            try:
                set_settings(name, id);
            except SettingsError as e:
                return {"status": "error",
                        "msg": f"invalid setting {name} = {id}"
                }
            get_db().commit()
            return {'status': 'success'}
        else:
            return {"status": "error",
                    "msg": f"{name} is not a known setting"
                    }
    else:
        return f"unsupported method {request.method}", 405


@bp.route('/json/<path>')
@debug_wrapper
def handleJSON(path, **kwargs):
    """
    Specialized endpoint called by jqgrid when populating tables
    """
    db = get_db()
    engine = db.get_bind()
    uiSession = session
    if path=='tourneys.json':
        tourneyList = [val for val in db.query(Tourney)]
        result = {
                  "records":len(tourneyList),  # total records
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
        result = {
                  "records":len(playerList),  # total records
                  "rows": [ {"id":p.id, "cell":[p.id, p.name, p.note]} for p in playerList ]
                  }
    elif path =='bouts.json':
        tourneyId = int(request.values.get('tourneyId', -1))
        if tourneyId >= 0:
            boutList = [b for b in db.query(Bout).filter_by(tourneyId=tourneyId)]
        else:
            boutList = [b for b in db.query(Bout)]
        result = {
                  "records":len(boutList),  # total records
                  "rows": [ {"id":p.boutId, "cell":[p.tourneyName, 
                                                    p.leftWins, p.lName, p.draws,
                                                    p.rName, p.rightWins, p.note] } 
                           for p in boutList ]
                  }
    elif path == 'horserace.json':
        paramList = ['%s:%s'%(str(k),str(v)) for k,v in list(request.values.items())]
        tourneyId = int(request.values['tourney'])
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
        playerList = [(p.id, p) for p in playerList]
        playerList.sort()
        playerList = [p for _, p in playerList]
        pList = [p for p in playerList]
        result = {
                  "records":len(pList),  # total records
                  "rows": [ {"id":p.id, "cell":[p.id, p.name, 0, str(p.weight), p.note, p.id]} 
                           for i,p in enumerate(pList) ]
                  }
    else:
        raise RuntimeError("Request for unknown AJAX element %s"%path)
    return result




