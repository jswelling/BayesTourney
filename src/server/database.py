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

def init_db():
    import models  # This defines the interface between classes and the db
    Base.metadata.create_all(bind=engine)
init_db()
    
