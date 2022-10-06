import click
from flask import current_app, g
from flask.cli import with_appcontext
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, column_property, scoped_session

Base = declarative_base()
metadata = Base.metadata

def _initialize_session_db():
    if (Path(__file__).parent.parent.parent / 'data').is_dir():
        default_database_path = Path(__file__).parent.parent.parent / 'data' / 'mydb.db'
    else:
        default_database_path = Path(current_app.instance_path) / 'mydb.db'
    default_database_uri = f"sqlite:///{default_database_path}"
    dbURI = current_app.config.get('SQLALCHEMY_DATABASE_URI', default_database_uri)
    current_app.logger.info(f'##### DBURI: {dbURI}')
    engine= create_engine(dbURI, echo=False)
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    return db_session, engine

def get_db():
    if 'db' not in g:
        g.db, g.engine = _initialize_session_db()
    return g.db

def get_engine():
    if 'engine' not in g:
        g.db, g.engine = _initialize_session_db()
    return g.engine

def init_db():
    # This defines the interface between classes and the db
    #Base.query = get_db().query_property()

    from . import models
    Base.metadata.create_all(bind=get_engine())

def close_db(e=None):
    db = g.pop('db', None)
    engine = g.pop('engine', None)
    if db is not None:
        db.close()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    from .models import User
    def load_user(user_id):
        try:
            user = get_db().query(User).filter_by(id=int(user_id)).one()
            return user
        except Exception as e:
            current_app.logger.warning(f'LOAD_USER exception {e} on {user_id} {type(user_id)}')
            return None
    app.login_manager.user_loader(load_user)
    app.login_manager.login_view = "auth.login"
