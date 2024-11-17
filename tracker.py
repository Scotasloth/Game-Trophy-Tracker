import sys
from customtkinter import *
import pyodbc
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import requests

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run browser in background 

    program_directory = sys.path[0]
    print (program_directory)
    #create(program_directory)
    getWebPage(chrome_options)

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
    
    # Close the database connection
    database.close()

def connect(db, dir):
    db_path = os.path.join(dir, db)
    conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + db_path)
    database = conn.cursor()
    print("Connection opened")
    return database

def getWebPage(chrome_options):
    url = ""

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        time.sleep(3)

        titles = driver.find_elements(By.TAG_NAME, '')

        for title in titles:
            print("Title Found", title.text)
    
    except Exception as e:
        print("Error", e)

    driver.quit()

if __name__ == '__main__':
    main()