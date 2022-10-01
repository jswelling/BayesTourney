#! /usr/bin/env python

'''
Created on Jun 4, 2013

@author: welling
'''

import io
import time
import json
import logging
import functools
from math import ceil
from pathlib import Path
from pprint import pprint

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

from .wrappers import debug_wrapper, debug_page_wrapper
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


logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


bp = Blueprint('legacy', __name__)


@bp.route('/experiment')
#@login_required
@debug_page_wrapper
def experiment():
    session.pop('horserace_includes')
    get_db().commit()
    return 'the experiment happened'


@bp.route('/hello')
def hello():
    return "Hello World"


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
        sortMe = list(pDict)
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
        raise RuntimeError(f"Sort index {sortIndex} not in field map")


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
            s += f"<option value={thisId}>{name}<option>\n"
        s += "</select>\n"
        return s
    elif path=='select_tourney':
        tourneyList = get_readable_tourneys(db)
        pairs = [((t.tourneyId,t.name)) for t in tourneyList]
        pairs.sort()
        s = "<select>\n"
        for thisId,name in pairs:
            s += f"<option value={thisId}>{name}<option>\n"
        s += "</select>\n"
        return s
    else:
        raise RuntimeError(f"Bad path /list/{path}")


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
            except NoResultFound as excinfo:
                raise RuntimeError("No such tourney") from excinfo
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
                raise RuntimeError(f'There is already a tourney named {name}')
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
            except NoResultFound as excinfo:
                raise RuntimeError("no such tourney") from excinfo
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
            except NoResultFound as excinfo:
                raise RuntimeError("no such bout") from excinfo
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
            except NoResultFound as excinfo:
                raise RuntimeError(f"No such bout {request.values['id']}") from excinfo
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
            except NoResultFound as excinfo:
                raise RuntimeError("No such entrant") from excinfo
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
            except NoResultFound as excinfo:
                raise RuntimeError("No such entrant") from excinfo
            with engine.connect() as conn:
                stxt = sql_text(
                    """
                    select * from bouts
                    where bouts.leftPlayerId = :p_id or bouts.rightPlayerId = :p_id
                    """
                )
                rs = conn.execute(stxt, p_id=player_id)
                num_bouts = len(list(rs))
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
        raise RuntimeError(f"Bad path /edit/{path}")


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
    #LOGGER.info(f"data: {data}")
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

    except RuntimeError as excinfo:
        LOGGER.info(f'horseRace_go exception: {excinfo}')
    result = {'image': output.getvalue(),
              'announce_html': fit_info.estimate_win_probabilities().as_html()
              }

    return result


@bp.route('/horserace_get_bouts_graph', methods=['POST'])
@debug_page_wrapper
@login_required
def horserace_get_bouts_graph(**kwargs):
    data = request.get_json()
    #LOGGER.info(f"data: {data}")
    player_df, bouts_df, checkbox_dict = _horserace_fetch_dataframes(
        data,
        **kwargs
    )
    tourney_id = int(data['tourney'])
    try:
        tourney = get_db().query(Tourney).filter_by(tourneyId=tourney_id).one()
    except NoResultFound as excinfo:
        raise RuntimeError("No such tourney") from excinfo
    check_can_read(tourney)

    try:
        fit_info = stat_utils.ModelFit.from_raw_bouts(
            player_df, bouts_df,
            draws_rule=get_settings()['hr_draws_rule']
        )
        svg_str = fit_info.gen_bouts_graph_svg()

    except RuntimeError as excinfo:
        LOGGER.info(f'horseRace_get_bouts_graph exception: {excinfo}')
    result = {'image': svg_str,
              'announce_html': f"Bouts for {tourney.name}"
              }

    return result


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


def _get_bearpit_dataframe(db, bouts):
    dict_list = []
    for bout in bouts:
        bout_tourney = db.query(Tourney).filter_by(tourneyId=bout.tourneyId).one()
        dct = {'tourneyName': bout_tourney.name,
               'leftWins': bout.leftWins,
               'leftPlayerName': bout.lName,
               'draws': bout.draws,
               'rightPlayerName': bout.rName,
               'rightWins': bout.rightWins,
               'note': bout.note,
               'bout_id': bout.boutId,
               'tourney_id': bout.tourneyId,
               'leftPlayerId': bout.leftPlayerId,
               'rightPlayerId': bout.rightPlayerId
               }
        dict_list.append(dct)
    if dict_list:
        boutDF = pd.DataFrame(dict_list)
        #print(boutDF.head())
        #print(boutDF.columns)

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

        settings_dict = get_settings()
        wt_win = {'bp_wins_2_pts': 2,
                  'bp_wins_1_pts': 1}[settings_dict['bp_wins_rule']]
        wt_draw = {'bp_draws_2_pts': 2,
                   'bp_draws_1_pts': 1,
                   'bp_draws_0_pts': 0}[settings_dict['bp_draws_rule']]
        wt_loss = {'bp_losses_1_pts': 1,
                   'bp_losses_0_pts': 0}[settings_dict['bp_losses_rule']]
        workDF['bearpit'] = (wt_win * workDF['wins'] + wt_loss * workDF['losses']
                             + wt_draw * workDF['draws'])
        workDF = workDF.sort_values(by='id', axis='rows')
    else:
        workDF = pd.DataFrame(columns=['playerName', 'id',
                                       'wins', 'losses', 'draws',
                                       'bouts', 'bearpit'])
    #print(workDF.head())
    #print(workDF.columns)
    return workDF


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
                player_id_set = set(val.id for val in player_rs)
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
                playerList = (list(rs1) + list(rs2))
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
            bout_list = list(db.query(Bout).filter_by(tourneyId=tourneyId).all())
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
        paramList = [f'{key}:{val}' for key, val in list(request.values.items())]
        tourneyId = int(request.values['tourney'])
        session['sel_tourney_id'] = tourneyId
        if tourneyId >= 0:
            tourney = (db.query(Tourney)
                       .filter_by(tourneyId=tourneyId)
                       .one()
                       )
            check_can_read(tourney)
            bouts = tourney.get_bouts(db)
        else:
            tourney_list = get_readable_tourneys(db)
            tourney_id_list = [tourney.tourneyId
                               for tourney in tourney_list]
            bouts = (db.query(Bout)
                     .filter(Bout.tourneyId.in_(tourney_id_list))
                     .all()
                     )

        workDF = _get_bearpit_dataframe(db, bouts)

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
        raise RuntimeError(f"Request for unknown AJAX element {path}")
    return result
