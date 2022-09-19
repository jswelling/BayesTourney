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
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.routing import BuildError
from werkzeug.exceptions import abort
from sqlalchemy.sql import text as sql_text
from sqlalchemy.exc import NoResultFound
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_svg import FigureCanvasSVG as FigureCanvas
from matplotlib.figure import Figure
from pathlib import Path
from pprint import pprint

from .database import get_db
from .models import (Tourney, LogitPlayer, Bout, User,
                     Group, TourneyPlayerPair, DBException)
from .settings import get_settings, set_settings, SettingsError
from .permissions import (
    get_readable_tourneys,
    get_readable_players,
    PermissionException,
    check_can_read, check_can_write, check_can_delete,
    current_user_can_read, current_user_can_write,
    )
from . import stat_utils


UPLOAD_ALLOWED_EXTENSIONS = ['tsv', 'csv']


logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

bp = Blueprint('', __name__)


@bp.app_errorhandler(PermissionException)
def handle_permission_exception(e):
    LOGGER.error(f"PermissionException: {e}")
    return f"{e}", 403


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
        #print('session state before view follows:')
        #pprint(session)
        rslt = view(**kwargs)
        #print('session follows:')
        #pprint(session)
        return rslt
    return wrapped_view

    
def allowed_upload_file(filename):
    return ('.' in filename and
            Path(filename).suffix[1:] in UPLOAD_ALLOWED_EXTENSIONS)


def insert_entrants_from_df(df):
    col_set = set([str(col) for col in df.columns])
    db = get_db()
    if set(["name", "note"]).issubset(col_set):
        df["id"] = df.apply(player_name_to_id,
                            key='name',
                            db=db,
                            axis=1)
        # Any row with an id of -1 is an unknown player
        for idx, row in df[df['id'] == -1].iterrows():
            LogitPlayer.create_unique(db, row['name'], row['note'])
        db.commit()
    else:
        raise DBException('Unknown column pattern for entrants')


@bp.route("/upload/entrants", methods=['POST'])
@debug_page_wrapper
@login_required
def upload_entrants_file():
    """
    This is an AJAX transaction
    """
    # check if the post request has the file part
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
    file_fullpath = Path(current_app.config['UPLOAD_FOLDER']) / filename
    LOGGER.info(f'Saving file to {filename}')
    file.save(file_fullpath)
    LOGGER.info('Save complete')
    if filename.endswith('.tsv'):
        df = pd.read_csv(file_fullpath, sep='\t')
    else:
        df = pd.read_csv(file_fullpath)
    LOGGER.info('Parse complete')
    try:
        insert_entrants_from_df(df)
    except DBException as e:
        LOGGER.info(f'DBException: {e}')
        return {"status":"failure", "msg":str(e)}
    LOGGER.info('Player creation complete')
    if 'tourney' in request.values:
        try:
            tourney_id = int(request.values['tourney'])
        except ValueError:
            LOGGER.info(msg := 'entrants upload tournament id has invalid format')
            return msg, 400
        if tourney_id <= 0:
            LOGGER.info(msg := 'entrants upload tournament id is not valid')
            return msg, 400
        db = get_db()
        tourney = db.query(Tourney).filter_by(tourneyId=tourney_id).one()
        check_can_write(tourney)
        for idx, row in df.iterrows():
            player = db.query(LogitPlayer).filter_by(name=row['name']).one()
            tourney.add_player(db, player)
        db.commit()
        LOGGER.info(f'Added {len(df)} players to the tournament {tourney.name}')
    file_fullpath.unlink()
    LOGGER.info('Uploaded file was unlinked')
    return {"status":"success"}


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
                note = row['note'] if 'note' in row else ""
                new_bout = Bout(int(row['tourneyId']),
                                int(row['leftWins']), int(row['leftPlayerId']),
                                int(row['draws']),
                                int(row['rightPlayerId']), int(row['rightWins']),
                                note = note)
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
    try:
        tourney = get_db().query(Tourney).filter_by(tourneyId=tourney_id).one()
    except NoResultFound:
        raise RuntimeError("No such tourney")
    LOGGER.info(f'Tourney is {tourney}')
    check_can_write(tourney)
    try:
        insert_bouts_from_df(df, tourney)
    except DBException as e:
        LOGGER.info(f'DBException: {e}')
        return {"status":"failure", "msg":str(e)}
    file_fullpath.unlink()
    LOGGER.info('Uploaded file was unlinked')
    return {"status":"success"}


@bp.route("/forms/entrants/create")
def forms_entrants_create():
    return render_template("forms_entrants_create.html");


@bp.route("/forms/tourneys/create")
def forms_tourneys_create():
    return render_template("forms_tourneys_create.html");


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


@bp.route("/admin_page")
def admin_page():
    return render_template("admin.html")


@bp.route('/')
@login_required
def index():
    return redirect(url_for('tourneys'))


@bp.route('/tourneys')
@login_required
@debug_page_wrapper
def tourneys():
    return render_template("tourneys.html")


@bp.route('/entrants')
@login_required
@debug_page_wrapper
def entrants():
    tourneyDict = {t.tourneyId: t.name for t in get_readable_tourneys(get_db())}
    return render_template("entrants.html",
                           sel_tourney_id=session.get('sel_tourney_id', -1),
                           tourneyDict=tourneyDict)


@bp.route('/bouts')
@login_required
@debug_page_wrapper
def bouts():
    tourneyDict = {t.tourneyId: t.name for t in get_readable_tourneys(get_db())}
    return render_template("bouts.html",
                           sel_tourney_id=session.get('sel_tourney_id', -1),
                           tourneyDict=tourneyDict)


@bp.route('/experiment')
#@login_required
@debug_page_wrapper
def experiment():
    session.pop('horserace_includes')
    get_db().commit()
    return 'the experiment happened'


@bp.route('/horserace')
@login_required
@debug_page_wrapper
def horserace():
    tourneyDict = {t.tourneyId: t.name for t in get_readable_tourneys(get_db())}
    return render_template("horserace.html",
                           sel_tourney_id=session.get('sel_tourney_id', -1),
                           tourneyDict=tourneyDict)


@bp.route('/hello')
def hello():
    return "Hello World"


@bp.route('/help')
@debug_page_wrapper
def help():
    return render_template("info.html")    


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
        tourneyList = get_readable_tourneys(db)
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
    Specialized endpoint that understands the requests jqgrid uses to perform
    edits, adds, and deletes.
    """
    db = get_db()
    engine = db.get_bind()
    if path=='tourneys':
        if request.values['oper']=='edit':
            try:
                t = db.query(Tourney).filter_by(tourneyId=int(request.values['id'])).one()
            except NoResultFound:
                raise RuntimeError("No such tourney")
            check_can_write(t)
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
            current_user_group = (db.query(Group)
                                  .filter_by(name=current_user.username)
                                  .one())
            t = Tourney(name, current_user.id, current_user_group.id, notes)
            check_can_write(t)
            db.add(t)
            db.commit()
            return {}
        elif request.values['oper']=='del':
            tourneyId = int(request.values['id'])
            try:
                tourney = db.query(Tourney).filter_by(tourneyId=tourneyId).one()
            except NoResultFound:
                raise RuntimeError("no such tourney")
            check_can_delete(tourney)
            bouts = db.query(Bout).filter_by(tourneyId=tourneyId)
            for bout in bouts:
                db.delete(bout)
            db.delete(tourney)
            db.commit()
            return {}
        else:
            raise RuntimeError(f"Bad edit operation {request.values['oper']}")
    elif path=='bouts':
        if request.values['oper']=='edit':
            try:
                b = db.query(Bout).filter_by(boutId=int(request.values['id'])).one()
            except NoResultFound:
                raise RuntimeError("no such bout")
            tourney = db.query(Tourney).filter_by(tourneyId=b.tourneyId).one()
            check_can_write(tourney)
            if 'tourney' in request.values:
                b.tourneyId = int(request.values['tourney'])
            if 'rightplayer' in request.values:
                b.rightPlayerId = int(request.values['rightplayer'])
            if 'leftplayer' in request.values:
                b.leftPlayerId = int(request.values['leftplayer'])
            if 'rwins' in request.values:
                b.rightWins = int(request.values['rwins'])
            if 'lwins' in request.values:
                b.leftWins = int(request.values['lwins'])
            if 'draws' in request.values:
                b.draws = int(request.values['draws'])
            if 'notes' in request.values:
                b.note = request.values['notes']
            db.commit()
            return {}
        elif request.values['oper']=='add':
            tourneyId = int(request.values['tourney'])
            tourney = db.query(Tourney).filter_by(tourneyId=tourneyId).one()
            check_can_write(tourney)
            lPlayerId = int(request.values['leftplayer'])
            rPlayerId = int(request.values['rightplayer'])
            lWins = int(request.values.get('lwins', '0'))
            rWins = int(request.values.get('rwins', '0'))
            draws = int(request.values.get('draws', '0'))
            note = request.values.get('notes', '')
            b = Bout(tourneyId, lWins, lPlayerId, draws,
                     rPlayerId, rWins, note)
            db.add(b)
            db.commit()
            return {}
        elif request.values['oper']=='del':
            try:
                b = db.query(Bout).filter_by(boutId=int(request.values['id'])).one()
            except NoResultFound:
                raise RuntimeError(f"No such bout")
            tourney = db.query(Tourney).filter_by(tourneyId=b.tourneyId).one()
            check_can_write(tourney)
            db.delete(b)
            db.commit()
            return {}
        else:
            raise RuntimeError(f"Bad edit operation {request.values['oper']}")
    elif path=='entrants':
        if request.values['oper']=='edit':
            try:
                p = db.query(LogitPlayer).filter_by(id=int(request.values['id'])).one()
            except NoResultFound:
                raise RuntimeError("No such entrant")
            if 'name' in request.values:
                p.name = request.values['name']
            if 'notes' in request.values:
                p.note = request.values['notes']
            db.commit()
            return {}
        elif request.values['oper']=='add':
            name = request.values['name']
            notes = request.values['notes']
            LogitPlayer.create_unique(db, name, notes)
            db.commit()
            return {}
        elif request.values['oper'] == 'del':
            player_id = int(request.values['id'])
            try:
                player = db.query(LogitPlayer).filter_by(id=player_id).one()
            except NoResultFound:
                raise RuntimeError("No such entrant")
            with engine.connect() as conn:
                stxt = sql_text(
                    """
                    select * from bouts
                    where bouts.leftPlayerId = :p_id or bouts.rightPlayerId = :p_id
                    """
                )
                rs = conn.execute(stxt, p_id=player_id)
                num_bouts = len([rec for rec in rs])
            if num_bouts == 0:
                db.delete(player)
                db.commit()
                return {"status":"success"}
            else:
                return {"status":"failure",
                        "msg":("The player could not be deleted because there"
                               " are bouts which include them")
                        }
        else:
            raise RuntimeError(f"Bad edit operation {request.values['oper']}")
    else:
        raise RuntimeError("Bad path /edit/%s"%path)


def _get_bouts_dataframe(tourneyId: int, include_ids: bool = False) -> pd.DataFrame:
    db = get_db()
    engine = db.get_bind()
    if tourneyId >= 0:
        tourney = db.query(Tourney).filter_by(tourneyId=tourneyId).one()
        check_can_read(tourney)
        if include_ids:
            boutDF = pd.read_sql(
                f"""
                select tourneys.name as tourneyName, 
                bouts.leftWins as leftWins, lplayers.name as leftPlayerName,
                lplayers.id as leftPlayerId,
                rplayers.name as rightPlayerName, 
                rplayers.id as rightPlayerId,
                bouts.rightWins as rightWins, 
                bouts.draws as draws, bouts.note as note
                from bouts, tourneys, players as lplayers, players as rplayers 
                where bouts.leftPlayerId = lplayers.id 
                and bouts.rightPlayerId = rplayers.id 
                and tourneys.tourneyId = bouts.tourneyId 
                and bouts.tourneyId = {tourneyId}
                """, engine, coerce_float=True)
        else:
            boutDF = pd.read_sql(
                f"""
                select tourneys.name as tourneyName, 
                bouts.leftWins as leftWins, lplayers.name as leftPlayerName, 
                rplayers.name as rightPlayerName, bouts.rightWins as rightWins, 
                bouts.draws as draws, bouts.note as note
                from bouts, tourneys, players as lplayers, players as rplayers 
                where bouts.leftPlayerId = lplayers.id 
                and bouts.rightPlayerId = rplayers.id 
                and tourneys.tourneyId = bouts.tourneyId 
                and bouts.tourneyId = {tourneyId}
                """, engine, coerce_float=True)
    else:
        raise RuntimeError('getting bouts from all tourneys is not implemented'
                           ' because it needs to support accessing only readable'
                           ' tournaments')
        if include_ids:
            boutDF = pd.read_sql(
                """
                select tourneys.name as tourneyName, 
                bouts.leftWins as leftWins, lplayers.name as leftPlayerName, 
                lplayers.id as leftPlayerId,
                rplayers.name as rightPlayerName, 
                rplayers.id as rightPlayerId,
                bouts.rightWins as rightWins, 
                bouts.draws as draws, bouts.note as note
                from bouts, tourneys, players as lplayers, players as rplayers 
                where bouts.leftPlayerId = lplayers.id 
                and bouts.rightPlayerId = rplayers.id 
                and tourneys.tourneyId = bouts.tourneyId 
                """, engine, coerce_float=True)
        else:
            boutDF = pd.read_sql(
                """
                select tourneys.name as tourneyName, 
                bouts.leftWins as leftWins, lplayers.name as leftPlayerName, 
                rplayers.name as rightPlayerName, bouts.rightWins as rightWins, 
                bouts.draws as draws, bouts.note as note
                from bouts, tourneys, players as lplayers, players as rplayers 
                where bouts.leftPlayerId = lplayers.id 
                and bouts.rightPlayerId = rplayers.id 
                and tourneys.tourneyId = bouts.tourneyId 
                """, engine, coerce_float=True)
    return boutDF


@bp.route('/download/bouts')
@login_required
@debug_page_wrapper
def handleBoutsDownloadReq(**kwargs):
    tourneyId = int(request.values.get('tourney', '-1'))
    boutDF = _get_bouts_dataframe(tourneyId)
    
    session_scratch_dir = current_app.config['SESSION_SCRATCH_DIR']
    full_path =  Path(session_scratch_dir) / 'bouts.tsv'
    boutDF.to_csv(full_path, sep='\t', index=False)
    return send_file(full_path, as_attachment=True)


def _get_entrants_dataframe(tourneyId: int, include_ids: bool = False) -> pd.DataFrame:
    db = get_db()
    engine = db.get_bind()
    if tourneyId >= 0:
        tourney = db.query(Tourney).filter_by(tourneyId=tourneyId).one()
        check_can_read(tourney)
        players = tourney.get_players(db)
    else:
        players = db.query(LogitPlayer).all()
    if include_ids:
        dict_list = [player.as_dict() for player in players
                     if current_user_can_read(player)]
    else:
        dict_list = [player.as_dict(include_id=False) for player in players
                     if current_user_can_read(player)]
    entrantDF = pd.DataFrame(dict_list)
    return entrantDF


@bp.route('/download/entrants')
@login_required
@debug_page_wrapper
def handleEntrantsDownloadReq(**kwargs):
    db = get_db()
    engine = db.get_bind()

    tourneyId = int(request.values.get('tourney', '-1'))
    if tourneyId > 0:
        tourney = db.query(Tourney).filter_by(tourneyId = tourneyId).one()
        tourney_name = tourney.name
    else:
        tourney_name = 'ALL_TOURNEYS'
    entrantDF = _get_entrants_dataframe(tourneyId)
    session_scratch_dir = current_app.config['SESSION_SCRATCH_DIR']
    full_path =  Path(session_scratch_dir) / f'entrants_{tourney_name}.tsv'
    entrantDF.to_csv(full_path, sep='\t', index=False)
    return send_file(full_path, as_attachment=True)


def _include_fun(row, keycols, checkbox_dict):
    flags = [checkbox_dict.get(row[keycol], False) for keycol in keycols]
    return all(flags)


def _horserace_fetch_dataframes(data, **kwargs):
    db = get_db()
    engine = db.get_bind()
    tourneyId = int(data['tourney'])
    if tourneyId >= 0:
        tourney = db.query(Tourney).filter_by(tourneyId=tourneyId).one()
        check_can_read(tourney)
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
    for player_id, flag in checkbox_dict.items():
        _set_hr_include(tourneyId, player_id, flag)
    playerDF = playerDF[playerDF.apply(_include_fun, axis=1,
                                       keycols=['id'], checkbox_dict=checkbox_dict)]
    boutDF = boutDF[boutDF.apply(_include_fun, axis=1,
                                 keycols=['leftPlayerId', 'rightPlayerId'],
                                 checkbox_dict=checkbox_dict)]

    return playerDF, boutDF, checkbox_dict


@bp.route('/horserace_go', methods=['POST'])
@debug_page_wrapper
@login_required
def horserace_go(**kwargs):
    data = request.get_json()
    #logMessage(f"data: {data}")
    playerDF, boutDF, checkbox_dict = _horserace_fetch_dataframes(data, **kwargs)
    output = io.StringIO()

    try:
        fit_info = stat_utils.estimate(
            playerDF, boutDF,
            draws_rule=get_settings()['hr_draws_rule']
        )
        plt.figure(figsize=[3,3])
        fig, axes = plt.subplots(ncols=1, nrows=1)
        graph_yscale_dct = {'hr_graph_yscale_linear': 'linear',
                            'hr_graph_yscale_log': 'log'}
        axes.set_yscale(graph_yscale_dct[get_settings()['hr_graph_yscale']])
        graph_type_dct = {'hr_graph_style_box': 'boxplot',
                          'hr_graph_style_violin': 'violin'}
        graph_type = graph_type_dct[get_settings()['hr_graph_style']]
        fit_info.gen_graph(fig, axes, graph_type)
        FigureCanvas(fig).print_svg(output)
        
    except RuntimeError as e:
        logMessage('horseRace_go exception: %s' % str(e))
    result = {'image': output.getvalue(),
              'announce_html': fit_info.estimate_win_probabilities().as_html()
              }

    return result
    

@bp.route('/horserace_get_bouts_graph', methods=['POST'])
@debug_page_wrapper
@login_required
def horserace_get_bouts_graph(**kwargs):
    data = request.get_json()
    #logMessage(f"data: {data}")
    player_df, bouts_df, checkbox_dict = _horserace_fetch_dataframes(
        data,
        **kwargs
    )
    tourney_id = int(data['tourney'])
    try:
        tourney = get_db().query(Tourney).filter_by(tourneyId=tourney_id).one()
    except NoResultFound:
        raise RuntimeError("No such tourney")
    check_can_read(tourney)

    try:
        fit_info = stat_utils.ModelFit.from_raw_bouts(
            player_df, bouts_df,
            draws_rule=get_settings()['hr_draws_rule']
        )
        svg_str = fit_info.gen_bouts_graph_svg()
        
    except RuntimeError as e:
        logMessage('horseRace_get_bouts_graph exception: %s' % str(e))
    result = {'image': svg_str,
              'announce_html': f"Bouts for {tourney.name}"
              }

    return result
    

def _tourney_json_rep(db, tourney):
    owner = db.query(User).filter_by(id=tourney.owner).one()
    group = db.query(Group).filter_by(id=tourney.group).one()
    rslt = {'id': tourney.tourneyId,
            'name': tourney.name,
            'note': tourney.note,
            'owner_name': owner.username,
            'group_name': group.name,
            'owner_read': tourney.owner_read,
            'owner_write': tourney.owner_write,
            'owner_delete': tourney.owner_delete,
            'group_read': tourney.group_read,
            'group_write': tourney.group_write,
            'group_delete': tourney.group_delete,
            'other_read': tourney.other_read,
            'other_write': tourney.other_write,
            'other_delete': tourney.other_delete,
            }
    return rslt


def _checkbox_value_map(map, key):
    rslt = key in map and map[key] and map[key] == 'on'
    return rslt


@bp.route('/ajax/tourneys/settings', methods=["GET", "PUT"])
@login_required
@debug_page_wrapper
def ajax_tourneys_settings(**kwargs):
    assert 'tourney_id' in request.values, 'tourney_id is a required parameter'
    tourney_id = int(request.values['tourney_id'])
    db = get_db()
    tourney = db.query(Tourney).filter_by(tourneyId=tourney_id).one()
    try:
        if request.method == 'GET':
            check_can_read(tourney)
            response_data = _tourney_json_rep(db, tourney)
            response_data.update({
                'current_user_groups': [grp.name for grp in current_user.get_groups(db)],
                'form_name': f'tourney_settings_dlg_form_{tourney.tourneyId}',
            })
            response_data['dlg_html'] = render_template("tourneys_settings_dlg.html",
                                                        **response_data)
            return {'status': 'success',
                    'value': response_data
                    }
        elif request.method == 'PUT':
            check_can_write(tourney)
            json_rep = _tourney_json_rep(db, tourney)
            changed = 0
            new_prot_state = {
                'group_name': request.values.get('group', tourney.groupName)
            }
            prot_keys = ['owner_read', 'owner_write', 'owner_delete',
                         'group_read', 'group_write', 'group_delete',
                         'other_read', 'other_write', 'other_delete']
            for key in prot_keys:
                new_prot_state[key] = _checkbox_value_map(request.values, key)
            if ((current_user_can_read(tourney, **new_prot_state)
                 and current_user_can_write(tourney, **new_prot_state))
                or request.values.get('confirm', 'false') == 'true'
                ):
                for key in prot_keys:
                    assert key in json_rep, "inconsistent protection keys"
                    if json_rep[key] != new_prot_state[key]:
                        setattr(tourney, key, new_prot_state[key])
                        json_rep[key] = new_prot_state[key]
                        changed += 1
            else:
                return {'status': 'confirm',
                        'msg': ("This change will make it impossible for you"
                                " to read or write this tournament. Are you sure?"
                                )
                        }
            if ('group' in request.values
                and json_rep['group_name'] != request.values['group']):
                new_group = db.query(Group).filter_by(name=request.values['group']).one()
                tourney.group = new_group.id
                json_rep['group_name'] = new_group.name
                changed += 1
            if changed:
                db.add(tourney)
                db.commit()
            else:
                logMessage(f'The tournament {tourney.name} was not changed')
            return {'status': 'success',
                    'value': json_rep
                    }
        else:
            return f"unsupported method {request.method}", 405
    except PermissionException as excinfo:
        return {'status': 'failure',
                'msg': f"{excinfo}"
                }


@bp.route('/ajax/tourneys', methods=["GET", "PUT"])
@login_required
@debug_page_wrapper
def ajax_tourneys(**kwargs):
    db = get_db()
    try:
        if request.method == 'GET':
            tourneys = get_readable_tourneys(db)
            rslt = {
                'status': 'success',
                'value': [tourney.as_dict() for tourney in tourneys]
                }
            if request.values.get('counts', 'false') == 'true':
                # Add counts info
                for row in rslt['value']:
                    row['bouts'] = (db.query(Bout)
                                    .filter(Bout.tourneyId == row['id'])
                                    .count())
                    row['entrants'] = (db.query(TourneyPlayerPair)
                                          .filter(TourneyPlayerPair.tourney_id == row['id'])
                                          .count())
            return rslt
        elif request.method == 'PUT':
            assert 'action' in request.values, 'action is required for PUT requests'
            if request.values['action'] == 'delete':
                assert 'tourney_id' in request.values, 'tourney_id is required for PUT "delete" requests'
                tourney_id = int(request.values['tourney_id'])
                tourney = db.query(Tourney).filter_by(tourneyId=tourney_id).one()
                check_can_delete(tourney)
                try:
                    tourney.full_delete(db)
                    db.commit()
                    return {
                        'status': 'success',
                        'value': {}
                    }
                except DBException as exc:
                    return {
                        'status': 'failure',
                        'msg': f'{exc}'
                    }
            elif request.values['action'] == 'create':
                assert 'tourney_id' not in request.values, 'tourney_id is forbidden for PUT "create" requests'
                assert 'name' in request.values, 'name is required for PUT "create" requests'
                name = request.values['name']
                assert 'note' in request.values, 'note is required for PUT "create" requests'
                note = request.values['note']
                try:
                    tourney = Tourney.create_unique(db, name, note)
                except DBException as exc:
                    return {
                        'status': 'failure',
                        'msg': f"{exc}"
                        }
                db.commit();
                return {
                    'status': 'success',
                    'value': { 'tourney_id': tourney.tourneyId }
                }
            else:
                return {
                    'status': 'failure',
                    'msg': f'unknown action "{action}" was requested'
                }
        else:
            return f"unsupported method {request.method}", 405
    except PermissionException as excinfo:
        return {'status': 'failure',
                'msg': f"{excinfo}"
                }


def _player_json_rep(db, player):
    rslt = {'id': player.id,
            'name': player.name,
            'note': player.note,
            }
    return rslt


@bp.route('/ajax/entrants/settings', methods=["GET", "PUT"])
@login_required
@debug_page_wrapper
def ajax_entrants_settings(**kwargs):
    assert 'player_id' in request.values, 'player_id is a required parameter'
    player_id = int(request.values['player_id'])
    db = get_db()
    player = db.query(LogitPlayer).filter_by(id=player_id).one()
    try:
        if request.method == 'GET':
            check_can_read(player)
            response_data = _player_json_rep(db, player)
            response_data.update({
                'form_name': f'player_settings_dlg_form_{player.id}',
            })
            response_data['dlg_html'] = render_template("player_settings_dlg.html",
                                                        **response_data)
            return {'status': 'success',
                    'value': response_data
                    }
        elif request.method == 'PUT':
            check_can_write(player)
            json_rep = _player_json_rep(db, player)
            changed = 0
            #
            # Permission management skeletonized because perms don't yet apply to players
            #
            new_prot_state = {
            }
            if ((current_user_can_read(player, **new_prot_state)
                 and current_user_can_write(player, **new_prot_state))
                or request.values.get('confirm', 'false') == 'true'
                ):
                pass
            else:
                return {'status': 'confirm',
                        'msg': ("This change will make it impossible for you"
                                " to read or write this tournament. Are you sure?"
                                )
                        }
            #
            # End skeletonized segment
            #
            for key in ['name', 'note']:
                cur_val = getattr(player, key)
                val = request.values.get(key, cur_val)
                if val != cur_val:
                    setattr(player, key, val)
                    json_rep[key] = val
                    changed += 1
            if changed:
                db.add(player)
                db.commit()
            else:
                logMessage(f'The player {player.name} was not changed')
            return {'status': 'success',
                    'value': json_rep
                    }
        else:
            return f"unsupported method {request.method}", 405
    except PermissionException as excinfo:
        return {'status': 'failure',
                'msg': f"{excinfo}"
                }


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
                get_db().commit()
                return {'status': 'success'}
            except SettingsError as e:
                return {"status": "error",
                        "msg": f"invalid setting {name} = {id}"
                }
        else:
            return {"status": "error",
                    "msg": f"{name} is not a known setting"
                    }
    else:
        return f"unsupported method {request.method}", 405


@bp.route('/ajax/entrants', methods=["GET", "PUT"])
@login_required
@debug_page_wrapper
def ajax_entrants(**kwargs):
    assert 'tourney_id' in request.values, 'tourney_id is a required parameter'
    tourney_id = int(request.values['tourney_id'])
    session['sel_tourney_id'] = tourney_id
    db = get_db()
    try:
        if request.method == 'GET':
            if tourney_id > 0:
                tourney = db.query(Tourney).filter_by(tourneyId=tourney_id).one()
                check_can_read(tourney)
                rslt = {
                    'status': 'success',
                    'value': [player.as_dict() for player in tourney.get_players(db)]
                }
            else:
                players = get_readable_players(db)
                rslt = {
                    'status': 'success',
                    'value': [player.as_dict() for player in players]
                }
            if request.values.get('counts', 'false') == 'true':
                # Add counts info
                for row in rslt['value']:
                    row['bouts'] = (db.query(Bout)
                                    .filter((Bout.leftPlayerId == row['id'])
                                             | (Bout.rightPlayerId == row['id']))
                                    .count())
                    row['tournaments'] = (db.query(Tourney).join(TourneyPlayerPair)
                                          .filter(TourneyPlayerPair.player_id == row['id'])
                                          .count())
            return rslt
        elif request.method == 'PUT':
            assert tourney_id > 0, 'invalid tourney id for PUT'
            tourney = db.query(Tourney).filter_by(tourneyId=tourney_id).one()
            check_can_write(tourney)
            assert 'action' in request.values, 'action is required for PUT requests'
            if request.values['action'] == 'add':
                assert 'player_id' in request.values, 'player_id is required for PUT "add" requests'
                player_id = int(request.values['player_id'])
                player = db.query(LogitPlayer).filter_by(id=player_id).one()
                tourney.add_player(db, player)
                db.commit()
                return {
                    'status': 'success',
                    'value': {}
                }
            elif request.values['action'] == 'delete':
                assert 'player_id' in request.values, 'player_id is required for PUT "delete" requests'
                player_id = int(request.values['player_id'])
                player = db.query(LogitPlayer).filter_by(id=player_id).one()
                tourney.remove_player(db, player)
                db.commit()
                return {
                    'status': 'success',
                    'value': {}
                }
            elif request.values['action'] == 'create':
                assert 'player_id' not in request.values, 'player_id is forbidden for PUT "create" requests'
                assert 'name' in request.values, 'name is required for PUT "create" requests'
                name = request.values['name']
                assert 'note' in request.values, 'note is required for PUT "create" requests'
                note = request.values['note']
                try:
                    player = LogitPlayer.create_unique(db, name, note)
                except DBException as exc:
                    return {
                        'status': 'failure',
                        'msg': f"{exc}"
                        }
                db.commit();
                tourney.add_player(db, player);
                db.commit();
                return {
                    'status': 'success',
                    'value': { 'player_id': player.id }
                }
            else:
                return {
                    'status': 'failure',
                    'msg': f'unknown action "{action}" was requested'
                }
        else:
            return f"unsupported method {request.method}", 405
    except PermissionException as excinfo:
        return {'status': 'failure',
                'msg': f"{excinfo}"
                }


def _get_hr_include(tourney_id, player_id):
    """
    All keys in the session must be strings, including the tourney_id and
    player_id used here.
    """
    dct = session.get('horserace_includes', {}).get(str(tourney_id), {})
    return dct.get(str(player_id), True)


def _set_hr_include(tourney_id, player_id, flag: bool):
    """
    All keys in the session must be strings, including the tourney_id and
    player_id used here.
    """
    dct = session.get('horserace_includes', {})
    tourney_dct = dct.get(str(tourney_id), {})
    tourney_dct[str(player_id)] = flag
    dct[str(tourney_id)] = tourney_dct
    session['horserace_includes'] = dct
    

@bp.route('/ajax/horserace/checkbox', methods=["GET", "PUT"])
@debug_wrapper
def handle_horserace_checkbox(**kwargs):
    try:
        tourney_id = int(request.values['tourney_id'])
        player_id = int(request.values['player_id'])
    except ValueError as e:
        return f"{e} missing or not an int", 400
    if request.method == "GET":
        return {"status": "success",
                "value": ("true" if _get_hr_include(tourney_id, player_id)
                          else "false")
                }
    elif request.method == "PUT":
        try:
            state = request.values['state']
        except ValueError as e:
            return f"{e} missing from request", 400
        bool_state = (state.lower() == 'true')
        _set_hr_include(tourney_id, player_id, bool_state)
        return {"status": "success",
                "value": ("true" if _get_hr_include(tourney_id, player_id)
                          else "false")
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
    if path=='tourneys':
        tourneyList = get_readable_tourneys(db)
        result = {
                  "records":len(tourneyList),  # total records
                  "rows": [ {"id":t.tourneyId,
                             "cell":[t.tourneyId,
                                     t.name,
                                     t.ownerName or '-nobody-',
                                     t.groupName or '-no group-',
                                     t.note,
                                     t.tourneyId]}
                           for t in tourneyList ]
                  }
    elif path=='entrants':
        tourneyId = int(request.values.get('tourneyId', -1))
        if tourneyId != -1:
            # we are dealing with a specific tourney
            tourney = (db.query(Tourney)
                       .filter_by(tourneyId=tourneyId)
                       .one()
                       )
            check_can_read(tourney)
        session['sel_tourney_id'] = tourneyId
        with engine.connect() as conn:
            rs1 = conn.execute(  # This gets the players with bouts
                """
                select players.name as name, players.id as id,
                  count(distinct bouts.tourneyId) as num_tournies,
                  count(boutId) as num_bouts, players.note as note
                from players, bouts
                where 
                  players.id = bouts.leftPlayerId
                  or players.id = bouts.rightPlayerId
                group by players.id
                """
            )
            if tourneyId >= 0:
                stxt = sql_text(
                    """
                    select players.id as id
                    from players, bouts
                    where
                      bouts.tourneyId = :t_id
                      and (players.id = bouts.leftPlayerId
                           or players.id = bouts.rightPlayerId)
                    """
                )
                player_rs = conn.execute(stxt, t_id=tourneyId)
                player_id_set = set([val.id for val in player_rs])
                playerList = [val for val in rs1 if val.id in player_id_set]
            else:
                rs2 = conn.execute(  # This gets the players without bouts
                    """
                    select players.name as name, players.id as id,
                      0 as num_tournies, 0 as num_bouts, players.note as note
                    from players, bouts
                    where 
                      players.id not in (select leftPlayerId from bouts)
                      and
                      players.id not in (select rightPlayerId from bouts)
                    group by players.id
                    """
                )
                playerList = ([val for val in rs1] + [val for val in rs2])
            result = {
                      "records":len(playerList),  # total records
                      "rows": [ {"id":p.id,
                                 "cell":[p.id, p.name,
                                         p.num_bouts, p.num_tournies,
                                         p.note]} for p in playerList ]
                      }
    elif path =='bouts':
        tourneyId = int(request.values.get('tourneyId', -1))
        session['sel_tourney_id'] = tourneyId
        if tourneyId >= 0:
            tourney = (db.query(Tourney)
                       .filter_by(tourneyId=tourneyId)
                       .one()
                       )
            check_can_read(tourney)
            bout_list = [b for b in (db.query(Bout)
                                     .filter_by(tourneyId=tourneyId)
                                     .all())]
        else:
            tourney_list = get_readable_tourneys(db)
            tourney_id_list = [tourney.tourneyId
                               for tourney in tourney_list]
            bout_list = (db.query(Bout)
                         .filter(Bout.tourneyId.in_(tourney_id_list))
                         .all()
                         )
            bout_id_list = [b.boutId for b in list(bout_list)]
        result = {
                  "records":len(bout_list),  # total records
                  "rows": [ {"id":p.boutId, "cell":[p.tourneyName, 
                                                    p.leftWins, p.lName, p.draws,
                                                    p.rName, p.rightWins, p.note] } 
                            for p in bout_list]
                  }
    elif path == 'horserace':
        paramList = ['%s:%s'%(str(k),str(v)) for k,v in list(request.values.items())]
        tourneyId = int(request.values['tourney'])
        session['sel_tourney_id'] = tourneyId

        boutDF = _get_bouts_dataframe(tourneyId, include_ids=True)
        #print(boutDF.head())

        leftDF = boutDF[['leftPlayerName', 'leftPlayerId', 'leftWins', 'rightWins',
                         'draws']].copy()
        leftDF['bouts'] = leftDF['leftWins'] + leftDF['rightWins'] + leftDF['draws']
        leftDF = leftDF.rename(columns={'leftWins': 'wins',
                                        'rightWins': 'losses',
                                        'leftPlayerName': 'playerName',
                                        'leftPlayerId': 'id'})

        rightDF = boutDF[['rightPlayerName', 'rightPlayerId', 'rightWins', 'leftWins',
                          'draws']].copy()
        rightDF['bouts'] = rightDF['leftWins'] + rightDF['rightWins'] + rightDF['draws']
        rightDF = rightDF.rename(columns={'leftWins': 'losses',
                                          'rightWins': 'wins',
                                          'rightPlayerName': 'playerName',
                                          'rightPlayerId': 'id'})
        rightDF = rightDF[leftDF.columns]

        workDF = pd.concat([leftDF, rightDF])
        workDF = workDF.groupby(['playerName', 'id']).sum().reset_index()

        bearpit_wt_dct = {  # tuples are weights for (wins, losses, draws)
            'hr_draws_rule_ignore': (2, 1, 0),
            'hr_draws_rule_win': (2, 1, 2),
            'hr_draws_rule_loss': (2, 1, 1)
        }
        wt_win, wt_loss, wt_draw = bearpit_wt_dct[get_settings()['hr_draws_rule']]
        workDF['bearpit'] = (wt_win * workDF['wins'] + wt_loss * workDF['losses']
                             + wt_draw * workDF['draws'])
        workDF = workDF.sort_values(by='id', axis='rows')
        print(workDF)
            
        result = {
                  "records":len(workDF),  # total records
                  "rows": [{"id":row['id'],
                            "cell":[row['id'], row['playerName'],
                                    row['wins'], row['losses'], row['draws'],
                                    row['bearpit'],
                                    str(row['id']) + ('+' if _get_hr_include(tourneyId,
                                                                             row['id'])
                                                      else '-')]} 
                            for _,row in workDF.iterrows() ]
                  }
    else:
        raise RuntimeError("Request for unknown AJAX element %s"%path)
    return result




