import json
from sqlalchemy import create_engine
from sqlalchemy.engine import url
from sqlalchemy.orm import sessionmaker, scoped_session, Query
import sqlparse
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_repr import RepresentableBase
from fantom_util.constants import FANTOM_WORKDIR

Base = declarative_base(cls=RepresentableBase)


with open(f"{FANTOM_WORKDIR}/.db_credentials.json", "r") as f:
    credentials = json.loads(f.read())

db_url = url.URL(
    drivername="postgresql",
    host=credentials["host"],
    username=credentials["user"],
    password=credentials["password"],
    database=credentials["dbname"],
)

engine = create_engine(db_url)

db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


def prettyprintable(statement, dialect=None, reindent=True):
    """Generate an SQL expression string with bound parameters rendered inline
    for the given SQLAlchemy statement. The function can also receive a
    `sqlalchemy.orm.Query` object instead of statement.
    can

    WARNING: Should only be used for debugging. Inlining parameters is not
             safe when handling user created data.
    """

    if isinstance(statement, Query):
        if dialect is None:
            dialect = statement.session.get_bind().dialect
        statement = statement.statement
    compiled = statement.compile(
        dialect=dialect, compile_kwargs={"literal_binds": True}
    )
    return sqlparse.format(str(compiled), reindent=reindent)
