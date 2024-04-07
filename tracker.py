import sys
from customtkinter import *
import pyodbc
import os

def main():

    program_directory = sys.path[0]
    print (program_directory)
    create(program_directory)

def create(dir):
    db_name = 'gamedata.accdb'
    
    # Connect to the Access database
    database = connect(db_name, dir)
    
    # Execute SQL to create a table
    try:
        database.execute('CREATE TABLE game (gameID INTEGER PRIMARY KEY, title TEXT NOT NULL)')
        print("Table 'game' created successfully.")
    except Exception as e:
        print("Error creating table:", e)

def connect(db, dir):
    db_path = os.path.join(dir, db)
    
    try:
        # Check if the directory exists
        if not os.path.exists(dir):
            print("Error: Directory does not exist.")
            return

        # Connect to the Access database
        database = pyodbc.connect(rf'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path}')
        cursor = database.cursor()
    
        return database
    except pyodbc.Error as e:
        print("pyodbc Error:", e)
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    main()