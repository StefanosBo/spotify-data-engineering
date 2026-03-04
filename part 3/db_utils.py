import sqlite3
import pandas as pd

def get_data(query):
    """
    Connects to the Spotify database, executes the SQL query, 
    and returns a Pandas DataFrame.
    """
    # Connect to the database
    conn = sqlite3.connect('spotify_database.db')
    
    # Execute query and load into DataFrame
    df = pd.read_sql_query(query, conn)
    
    # Close the connection to free up resources
    conn.close()
    
    return df

