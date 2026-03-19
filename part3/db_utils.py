import sqlite3
import pandas as pd
import os

# Resolve DB path: check current directory, then part3/, then data/
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)

DB_PATH = os.path.join(os.getcwd(), 'spotify_database.db')
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(_THIS_DIR, 'spotify_database.db')
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(_PROJECT_ROOT, 'data', 'spotify_database.db')


def get_data(query, params=()):
    """
    Connects to the Spotify database, executes the SQL query,
    and returns a Pandas DataFrame.
    Supports parameterized queries via the params argument.
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
