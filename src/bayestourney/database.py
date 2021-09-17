import click
from flask import current_app, g
from flask.cli import with_appcontext
from pathlib import Path

dbURI = f"sqlite:///{Path(__file__).parent.parent.parent / 'data' / 'mydb.db'}"
print(f'##### DBURI: {dbURI}')

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, column_property, scoped_session

engine= create_engine(dbURI, echo=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def get_db():
    if 'db' not in g:
        g.db = db_session
    return g.db

def get_engine():
    if 'engine' not in g:
        g.engine = engine
    return g.engine

def init_db():
    # This defines the interface between classes and the db
    from . import models
    Base.metadata.create_all(bind=engine)

def close_db(e=None):
    db = g.pop('db', None)
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
