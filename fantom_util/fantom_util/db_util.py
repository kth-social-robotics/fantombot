import psycopg2
import json

from fantom_util.constants import FANTOM_WORKDIR

def connect_db(named_tuple_cursor=False):
    with open(f'{FANTOM_WORKDIR}/.db_credentials.json', "r") as f:
        credentials = json.loads(f.read())
    try:
        conn = psycopg2.connect(**credentials)
        if named_tuple_cursor:
            cur = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
        else:
            cur = conn.cursor()
    except:
        print("I am unable to connect to the database")
    return conn, cur
