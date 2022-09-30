#! /usr/bin/env python

'''
Created on Jun 4, 2013

@author: welling
'''

import json
import logging
from pathlib import Path
from pprint import pprint

from flask import (
    Blueprint, flash, render_template, request, url_for,
    send_file, session, redirect, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.routing import BuildError
from sqlalchemy.exc import NoResultFound
import pandas as pd

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
from .legacy_endpoints import bp as legacy_bp, _get_bearpit_dataframe


UPLOAD_ALLOWED_EXTENSIONS = ['tsv', 'csv']


logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


bp = Blueprint('', __name__)
bp.register_blueprint(legacy_bp)


@bp.app_errorhandler(PermissionException)
def handle_permission_exception(e):
    LOGGER.error(f"PermissionException: {e}")
    return f"{e}", 403


@bp.app_errorhandler(DBException)
def handle_db_exception(e):
    LOGGER.error(f"DBException: {e}")
    return f"{e}", 403


def allowed_upload_file(filename):
    return ('.' in filename and
            Path(filename).suffix[1:] in UPLOAD_ALLOWED_EXTENSIONS)


def insert_entrants_from_df(df):
    col_set = set(str(col) for col in df.columns)
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
    if 'tourney_id' in request.values:
        try:
            tourney_id = int(request.values['tourney_id'])
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
    try:
        return db.query(LogitPlayer).filter_by(name=row[key]).one().id
    except NoResultFound:
        return -1  # we need to use an int as the signal value for Pandas' sake


def insert_bouts_from_df(df, tourney):
    col_set = set(str(col) for col in df.columns)
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
        if bad_name_l := list(bad_names.unique()):
            bad_name_str = ', '.join([f'"{nm}"' for nm in bad_name_l])
            raise DBException(f'Unknown or multiply defined player names: {bad_name_str}')
        bad_names = []
        for idx, row in df.iterrows():
            if (db.query(TourneyPlayerPair)
                .filter(TourneyPlayerPair.tourney_id == row['tourneyId'],
                        TourneyPlayerPair.player_id == row['leftPlayerId'])
                .first()) is None:
                bad_names.append(row['leftPlayerName'])
            if (db.query(TourneyPlayerPair)
                .filter(TourneyPlayerPair.tourney_id == row['tourneyId'],
                        TourneyPlayerPair.player_id == row['rightPlayerId'])
                .first()) is None:
                bad_names.append(row['rightPlayerName'])
        if bad_names:
            bad_names = list(set(bad_names))  # remove duplicates
            raise DBException("The following players were not entered in the tourney"
                              f" {tourney.name}: {', '.join(bad_names)}.  Do you need"
                              " to import a table of entrants first?")
        df = df.drop(columns=['leftPlayerName', 'rightPlayerName', 'tourneyName'])
        for idx, row in df.iterrows():
            note = row['note'] if 'note' in row else ""
            new_bout = Bout(int(row['tourneyId']),
                            int(row['leftWins']), int(row['leftPlayerId']),
                            int(row['draws']),
                            int(row['rightPlayerId']), int(row['rightWins']),
                            note = note)
            db.add(new_bout)
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
    if 'tourney_id' in request.values:
        tourney_id_str = request.values['tourney_id']
    else:
        LOGGER.info(msg := 'bout upload tourney_id is missing')
        return msg, 400
    try:
        tourney_id = int(tourney_id_str)
    except ValueError:
        LOGGER.info(msg := 'bout upload tourney_id invalid format')
        return msg, 400
    if tourney_id < 0:
        LOGGER.info(msg := 'bout upload tourney_id is not valid')
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
    except NoResultFound as exc:
        raise RuntimeError("No such tourney") from exc
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
    return render_template("forms_entrants_create.html")


@bp.route("/forms/tourneys/create")
def forms_tourneys_create():
    return render_template("forms_tourneys_create.html")


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
    return render_template("site_map.html", link_dict=dict(links))


@bp.route("/settings")
def settings():
    return render_template("prefs.html", **(get_settings()))


@bp.route("/admin_page")
def admin_page():
    return render_template("admin.html")


@bp.route('/')
@login_required
def index():
    return redirect(url_for('tourneys_fun'))


@bp.route('/tourneys')
@login_required
@debug_page_wrapper
def tourneys_fun():
    return render_template("tourneys.html")


@bp.route('/entrants')
@login_required
@debug_page_wrapper
def entrants_fun():
    if 'tourney_id' in request.values:
        tourney_id = int(request.values['tourney_id'])
        session['sel_tourney_id'] = tourney_id
    tourneyDict = {t.tourneyId: t.name for t in get_readable_tourneys(get_db())}
    return render_template("entrants.html",
                           sel_tourney_id=session.get('sel_tourney_id', -1),
                           tourneyDict=tourneyDict)


@bp.route('/bouts')
@login_required
@debug_page_wrapper
def bouts_fun():
    db = get_db()
    if 'tourney_id' in request.values:
        tourney_id = int(request.values['tourney_id'])
        session['sel_tourney_id'] = tourney_id
    tourneyDict = {t.tourneyId: t.name for t in get_readable_tourneys(db)}
    tourney_id = session.get('sel_tourney_id', -1)
    if tourney_id < 0:
        players = get_readable_players(db)
    else:
        assert tourney_id in tourneyDict, 'current user cannot read this tourney'
        tourney = db.query(Tourney).filter_by(tourneyId=tourney_id).one()
        players = tourney.get_players(db)
    playerDict = {player.id: player.name for player in players}
    return render_template("bouts.html",
                           sel_tourney_id=tourney_id,
                           tourneyDict=tourneyDict,
                           playerDict=playerDict)


@bp.route('/horserace')
@login_required
@debug_page_wrapper
def horserace_fun():
    tourneyDict = {t.tourneyId: t.name for t in get_readable_tourneys(get_db())}
    return render_template("horserace.html",
                           sel_tourney_id=session.get('sel_tourney_id', -1),
                           tourneyDict=tourneyDict)


@bp.route('/help')
@debug_page_wrapper
def help_fun():
    return render_template("info.html")


@bp.route('/notimpl')
@debug_page_wrapper
def notimplPage():
    return render_template('notimpl.html')


def _get_bouts_dataframe(tourneyId: int, include_ids: bool = False) -> pd.DataFrame:
    db = get_db()
    if tourneyId >= 0:
        tourney = db.query(Tourney).filter_by(tourneyId=tourneyId).one()
        check_can_read(tourney)
        bouts = tourney.get_bouts(db)
    else:
        tourneys = get_readable_tourneys(db)
        tourney_id_list = [tourney.tourneyId for tourney in tourneys]
        bouts = db.query(Bout).filter(Bout.tourneyId.in_(tourney_id_list)).all()
    dict_list = []
    for bout in bouts:
        bout_tourney = db.query(Tourney).filter_by(tourneyId=bout.tourneyId).one()
        dct = {'tourneyName': bout_tourney.name,
               'leftWins': bout.leftWins,
               'leftPlayerName': bout.lName,
               'draws': bout.draws,
               'rightPlayerName': bout.rName,
               'rightWins': bout.rightWins,
               'note': bout.note}
        if include_ids:
            dct['bout_id'] = bout.boutId
            dct['tourney_id'] = bout.tourneyId
            dct['leftPlayerId'] = bout.leftPlayerId
            dct['rightPlayerId'] = bout.rightPlayerId
        dict_list.append(dct)
    boutDF = pd.DataFrame(dict_list)
    return boutDF


@bp.route('/download/bouts')
@login_required
@debug_page_wrapper
def handleBoutsDownloadReq(**kwargs):
    db = get_db()
    tourneyId = int(request.values.get('tourney_id', '-1'))
    if tourneyId > 0:
        tourney = db.query(Tourney).filter_by(tourneyId = tourneyId).one()
        tourney_name = tourney.name
    else:
        tourney_name = 'ALL_TOURNEYS'
    boutDF = _get_bouts_dataframe(tourneyId)

    session_scratch_dir = current_app.config['SESSION_SCRATCH_DIR']
    full_path =  Path(session_scratch_dir) / f'bouts_{tourney_name}.tsv'
    boutDF.to_csv(full_path, sep='\t', index=False)
    return send_file(full_path, as_attachment=True)


def _get_entrants_dataframe(tourneyId: int, include_ids: bool = False) -> pd.DataFrame:
    db = get_db()
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
    tourneyId = int(request.values.get('tourney_id', '-1'))
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


def _horserace_dataframes(db, tourneys, checkboxes):
    bouts = {}
    players = {}
    for tourney in tourneys:
        check_can_read(tourney)
        for bout in tourney.get_bouts(db):
            bouts[bout.boutId] = bout
        for player in tourney.get_players(db):
            players[player.id] = player
    boutDF = pd.DataFrame(bout.as_dict() for bout in bouts.values())
    playerDF = pd.DataFrame(player.as_dict() for player in players.values())
    checkbox_dict = {int(k): v for k, v in checkboxes.items()}
    playerDF = playerDF[playerDF.apply(_include_fun, axis=1,
                                       keycols=['id'], checkbox_dict=checkbox_dict)]
    boutDF = boutDF[boutDF.apply(_include_fun, axis=1,
                                 keycols=['lplayer_id', 'rplayer_id'],
                                 checkbox_dict=checkbox_dict)]
    return boutDF, playerDF, checkbox_dict


def _get_include_flag(row, tourney_id):
    return _get_hr_include(tourney_id,row['id'])


@bp.route('/download/horserace')
@login_required
@debug_page_wrapper
def handleBearpitDownloadReq(**kwargs):
    db = get_db()
    tourneyId = int(request.values.get('tourney_id', '-1'))
    if tourneyId > 0:
        tourney = db.query(Tourney).filter_by(tourneyId = tourneyId).one()
        check_can_read(tourney)
        tourney_name = tourney.name
        bouts = tourney.get_bouts(db)
    else:
        tourneys = get_readable_tourneys(db)
        tourney_name = 'ALL_TOURNEYS'
        tourney_id_list = [tourney.tourneyId for tourney in tourneys]
        bouts = (db.query(Bout)
                 .filter(Bout.tourneyId.in_(tourney_id_list))
                 .all()
                 )
    bearpitDF = _get_bearpit_dataframe(db, bouts)
    bearpitDF['include'] = bearpitDF.apply(_get_include_flag,
                                           axis=1, tourney_id=tourneyId)

    session_scratch_dir = current_app.config['SESSION_SCRATCH_DIR']
    full_path =  Path(session_scratch_dir) / f'bearpit_{tourney_name}.tsv'
    bearpitDF.to_csv(full_path, sep='\t', index=False)
    return send_file(full_path, as_attachment=True)


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
                if key in request.values:
                    new_prot_state[key] = (request.values[key] in [True, 'true', 'True'])
                else:
                    new_prot_state[key] = json_rep[key]
            if ((current_user_can_read(tourney, **new_prot_state)
                 and current_user_can_write(tourney, **new_prot_state))
                or request.values.get('confirm', 'false') == 'true'
                ):
                for key in prot_keys:
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
            if ('name' in request.values
                and json_rep['name'] != request.values['name']):
                json_rep['name'] = tourney.name = request.values['name']
                changed += 1
            if ('note' in request.values
                and json_rep['note'] != request.values['note']):
                json_rep['note'] = tourney.note = request.values['note'].strip()
                changed += 1
            if changed:
                db.add(tourney)
                db.commit()
            else:
                LOGGER.info(f'The tournament {tourney.name} was not changed')
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
                assert 'tourney_id' in request.values, ('tourney_id is required for PUT'
                                                        ' "delete" requests')
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
                assert 'tourney_id' not in request.values, ('tourney_id is forbidden for'
                                                            ' PUT "create" requests')
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
                db.commit()
                return {
                    'status': 'success',
                    'value': { 'tourney_id': tourney.tourneyId }
                }
            else:
                action = request.values['action']
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
            response_data = player.as_dict()
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
            json_rep = player.as_dict()
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
                LOGGER.info(f'The player {player.name} was not changed')
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
                'value': dict(get_settings().items())
                }
    elif request.method == 'PUT':
        name = request.values['name']
        setting_id = request.values['id']
        if name in get_settings():
            try:
                set_settings(name, setting_id)
                get_db().commit()
                return {'status': 'success'}
            except SettingsError:
                return {"status": "error",
                        "msg": f"invalid setting {name} = {setting_id}"
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
    if tourney_id > 0:  # only update session tourney for specific requests
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
                assert 'player_id' in request.values, ('player_id is required for'
                                                       ' PUT "delete" requests')
                player_id = int(request.values['player_id'])
                player = db.query(LogitPlayer).filter_by(id=player_id).one()
                tourney.remove_player(db, player)
                db.commit()
                return {
                    'status': 'success',
                    'value': {}
                }
            elif request.values['action'] == 'create':
                assert 'player_id' not in request.values, ('player_id is forbidden for'
                                                           ' PUT "create" requests')
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
                db.commit()
                tourney.add_player(db, player)
                db.commit()
                return {
                    'status': 'success',
                    'value': { 'player_id': player.id }
                }
            else:
                action = request.values['action']
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


@bp.route('/ajax/bouts/settings', methods=["GET", "PUT"])
@login_required
@debug_page_wrapper
def ajax_bouts_settings(**kwargs):
    assert 'bout_id' in request.values, 'bout_id is a required parameter'
    bout_id = int(request.values['bout_id'])
    db = get_db()
    bout = db.query(Bout).filter_by(boutId=bout_id).one()
    tourney = db.query(Tourney).filter_by(tourneyId=bout.tourneyId).one()
    lplayer = db.query(LogitPlayer).filter_by(id=bout.leftPlayerId).one()
    rplayer = db.query(LogitPlayer).filter_by(id=bout.rightPlayerId).one()
    try:
        if request.method == 'GET':
            check_can_read(tourney)
            check_can_read(lplayer)
            check_can_read(rplayer)
            player_dict = {player.id: player.name for player in tourney.get_players(db)}
            response_data = bout.as_dict()
            response_data.update({
                'form_name': f'bout_settings_dlg_form_{bout.boutId}',
            })
            response_data['dlg_html'] = render_template("bout_settings_dlg.html",
                                                        player_dict=player_dict,
                                                        **response_data)
            return {'status': 'success',
                    'value': response_data
                    }
        elif request.method == 'PUT':
            check_can_write(tourney)
            check_can_read(lplayer)
            check_can_read(rplayer)
            json_rep = bout.as_dict()
            change_dct = {}
            for key in json_rep:
                # The request comes back with player ids in the name slots;
                # we must map those to the corresponding ids
                mapped_key = {'lplayer': 'lplayer_id',
                            'rplayer': 'rplayer_id'}.get(key, key)
                new_val = request.values.get(key, json_rep[mapped_key])
                if key in ['lwins', 'rwins', 'draws', 'lplayer', 'rplayer']:
                    new_val = int(new_val)
                if new_val != json_rep[mapped_key]:
                    change_dct[mapped_key] = new_val
            if change_dct:
                bout.update_from_dict(change_dct)
                json_rep.update(change_dct)
                db.add(bout)
                db.commit()
            else:
                LOGGER.info(f'Bout {bout.boutId} was not changed')
            json_rep['lplayer'] = bout.lName
            json_rep['rplayer'] = bout.rName
            return {'status': 'success',
                    'value': json_rep
                    }
        else:
            return f"unsupported method {request.method}", 405
    except PermissionException as excinfo:
        return {'status': 'failure',
                'msg': f"{excinfo}"
                }


@bp.route('/ajax/bouts', methods=["GET", "PUT"])
@login_required
@debug_page_wrapper
def ajax_bouts(**kwargs):
    db = get_db()
    try:
        if request.method == 'GET':
            assert 'tourney_id' in request.values, 'tourney_id is required for Bout GET requests'
            tourney_id = int(request.values['tourney_id'])
            if tourney_id > 0:  # only update session tourney for specific requests
                session['sel_tourney_id'] = tourney_id
            if tourney_id > 0:
                tourney = db.query(Tourney).filter_by(tourneyId=tourney_id).one()
                check_can_read(tourney)
                rslt = {
                    'status': 'success',
                    'value': [bout.as_dict() for bout in tourney.get_bouts(db)]
                }
            else:
                tourneys = get_readable_tourneys(db)
                tourney_id_list = [tourney.tourneyId for tourney in tourneys]
                bouts = (db.query(Bout)
                         .filter(Bout.tourneyId.in_(tourney_id_list))
                         .all()
                         )
                rslt = {
                    'status': 'success',
                    'value': [bout.as_dict() for bout in bouts]
                }
            return rslt
        elif request.method == 'PUT':
            assert 'action' in request.values, 'action is required for PUT requests'
            if request.values['action'] == 'add':
                for key in ['tourney_id', 'lplayer', 'rplayer']:
                    assert key in request.values, f'{key} is required for PUT "add" requests'
                if not any(key in request.values for key in ['lwins', 'rwins', 'draws',
                                                             'note']):
                    raise AssertionError('At least one of lwins, rwins, draws, or note'
                                         'is required for PUT "add" requests')
                tourney_id = int(request.values['tourney_id'])
                lplayer_id = int(request.values['lplayer'])
                rplayer_id = int(request.values['rplayer'])
                lwins = int(request.values.get('lwins', 0))
                rwins = int(request.values.get('rwins', 0))
                draws = int(request.values.get('draws', 0))
                note = request.values.get('note', '')
                tourney = db.query(Tourney).filter_by(tourneyId=tourney_id).one()
                check_can_write(tourney)
                try:
                    bout = Bout.checked_create(db, tourney_id,lwins, lplayer_id,
                                               draws,
                                               rplayer_id, rwins,
                                               note)
                except DBException as excinfo:
                    return {
                        'status': 'failure',
                        'msg': f'{excinfo}'
                        }
                db.add(bout)
                db.commit()
                return {
                    'status': 'success',
                    'value': {}
                }
            elif request.values['action'] == 'delete':
                assert 'bout_id' in request.values, 'bout_id is required for PUT "delete" requests'
                bout_id = int(request.values['bout_id'])
                bout = db.query(Bout).filter_by(boutId=bout_id).one()
                tourney = db.query(Tourney).filter_by(tourneyId=bout.tourneyId).one()
                check_can_write(tourney)
                db.delete(bout)
                db.commit()
                return {
                    'status': 'success',
                    'value': {}
                }
        else:
            return f"unsupported method {request.method}", 405
    except PermissionException as excinfo:
        return {'status': 'failure',
                'msg': f"{excinfo}"
                }
    raise RuntimeError("logic error - this should not be reached")


@bp.route('/ajax/bearpit', methods=["GET", "PUT"])
@login_required
@debug_page_wrapper
def ajax_bearpit(**kwargs):
    db = get_db()
    assert 'tourney_id' in request.values, 'tourney_id is required for Bearpit requests'
    tourney_id = int(request.values['tourney_id'])
    try:
        if request.method == 'GET':
            if tourney_id > 0:  # only update session tourney for specific requests
                session['sel_tourney_id'] = tourney_id
            if tourney_id > 0:
                tourney = db.query(Tourney).filter_by(tourneyId=tourney_id).one()
                check_can_read(tourney)
                bouts = tourney.get_bouts(db)
            else:
                tourneys = get_readable_tourneys(db)
                tourney_id_list = [tourney.tourneyId for tourney in tourneys]
                bouts = (db.query(Bout)
                         .filter(Bout.tourneyId.in_(tourney_id_list))
                         .all()
                         )
            workDF = _get_bearpit_dataframe(db, bouts)
            rslt = {
                'status': 'success',
                #'value': [bout.as_dict() for bout in bouts]
                'value': [{'id': row['id'],
                           'name': row['playerName'],
                           'wins': row['wins'],
                           'losses': row['losses'],
                           'draws': row['draws'],
                           'bearpit': row['bearpit'],
                           'include': 1 if _get_hr_include(tourney_id,row['id']) else 0
                           }
                          for _, row in workDF.iterrows()]
            }
            return rslt
        elif request.method == 'PUT':
            assert 'action' in request.values, 'action is required for PUT requests'
            raise NotImplementedError
        else:
            return f"unsupported method {request.method}", 405
    except PermissionException as excinfo:
        return {'status': 'failure',
                'msg': f"{excinfo}"
                }


@bp.route('/ajax/wfw', methods=["POST"])
@login_required
@debug_page_wrapper
def ajax_wfw(**kwargs):
    db = get_db()
    assert 'tourney_id' in request.values, 'tourney_id is required for wfw requests'
    assert 'checkboxes' in request.values, 'checkboxes is required for wfw requests'
    tourney_id = int(request.values['tourney_id'])
    try:
        if request.method == 'POST':
            if tourney_id > 0:
                tourney = db.query(Tourney).filter_by(tourneyId=tourney_id).one()
                check_can_read(tourney)
                tourneys = [tourney]
                label_str = tourney.name
            else:
                tourneys = get_readable_tourneys(db)
                label_str = f'{len(tourneys)} tournaments'
            checkbox_dict = json.loads(request.values['checkboxes'])
            boutDF, playerDF, checkbox_dict = _horserace_dataframes(db, tourneys,
                                                                    checkbox_dict)
            try:
                fit_info = stat_utils.ModelFit.from_raw_bouts(
                    playerDF, boutDF,
                    draws_rule=get_settings()['hr_draws_rule']
                )
                svg_str = fit_info.gen_bouts_graph_svg()
            except RuntimeError as excinfo:
                LOGGER.info(f'ajax_wfw exception: {excinfo}')
                raise
            response_data = {
                'image': svg_str,
                'label_str': label_str
            }
            response_data['dlg_html'] = render_template("horserace_who_fought_who_dlg.html",
                                                        **response_data)
            return {'status': 'success',
                    'value': response_data
                    }
        else:
            return f"unsupported method {request.method}", 405
    except PermissionException as excinfo:
        return {'status': 'failure',
                'msg': f"{excinfo}"
                }


@bp.route('/ajax/whoiswinning', methods=["POST"])
@login_required
@debug_page_wrapper
def ajax_whoiswinning(**kwargs):
    db = get_db()
    assert 'tourney_id' in request.values, 'tourney_id is required for wfw requests'
    assert 'checkboxes' in request.values, 'checkboxes is required for wfw requests'
    tourney_id = int(request.values['tourney_id'])
    try:
        if request.method == 'POST':
            if tourney_id > 0:
                tourney = db.query(Tourney).filter_by(tourneyId=tourney_id).one()
                check_can_read(tourney)
                tourneys = [tourney]
                label_str = tourney.name
            else:
                tourneys = get_readable_tourneys(db)
                label_str = f'{len(tourneys)} tournaments'
            checkbox_dict = json.loads(request.values['checkboxes'])
            boutDF, playerDF, checkbox_dict = _horserace_dataframes(db, tourneys,
                                                                    checkbox_dict)
            print(boutDF.head())
            print(playerDF.head())
            pprint(checkbox_dict)
            try:
                fit_info = stat_utils.ModelFit.from_raw_bouts(
                    playerDF, boutDF,
                    draws_rule=get_settings()['hr_draws_rule']
                )
                graph_yscale_dct = {'hr_graph_yscale_linear': 'linear',
                                    'hr_graph_yscale_log': 'log'}
                graph_yscale = graph_yscale_dct[get_settings()['hr_graph_yscale']]
                graph_type_dct = {'hr_graph_style_box': 'boxplot',
                                  'hr_graph_style_violin': 'violin'}
                graph_type = graph_type_dct[get_settings()['hr_graph_style']]
                svg_str = fit_info.gen_horserace_graph_svg(graph_yscale, graph_type)
                announce_html = fit_info.estimate_win_probabilities().as_html()

            except RuntimeError as excinfo:
                LOGGER.info(f'ajax_whoiswinning exception: {excinfo}')
                raise
            response_data = {
                'image': svg_str,
                'label_str': label_str,
                'announce_html': announce_html
            }
            response_data['dlg_html'] = render_template("horserace_who_is_winning_dlg.html",
                                                        **response_data)
            return {'status': 'success',
                    'value': response_data
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
        print('POINT 1')
        pprint(request.values)
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
