import os
import pyodbc
import sys

db = 'gamedata.accdb'  # Database file name
dir = sys.path[0]

def connect():
    """Connect to the Access database and return a database cursor."""
    db_path = os.path.join(dir, db)  # Path to the database file
    conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + db_path)  # ODBC connection string
    database = conn.cursor()  # Create a cursor for executing SQL queries
    print("Connection opened")
    return database