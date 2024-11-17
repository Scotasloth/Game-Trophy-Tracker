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
    program_directory = sys.path[0]
    print (program_directory)

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run browser in background 

    root = CTk(className="Trophy Tracker") 
    root.geometry("590x500")
    root.title("Trophy Tracker")

    set_appearance_mode("dark")

    CTkButton(master = root, text = "Initialize", command = create(program_directory)).place(relx = .01, rely = .5)
    CTkButton(master = root, text = "Add new Trophy").place(relx = .7, rely = .5)
    CTkButton(master = root, text = "Add new game", command = newGame(root, chrome_options)).place(relx = .4, rely = .5)

    root.mainloop()

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

def newGame(root, chrome_options):
    game = ""
    addGame = CTkToplevel(root)
    addGame.title("Add New Game")
    addGame.geometry("400x300")

    CTkEntry(master = addGame, placeholder_text= "What is the new game?", textvariable = game).place(relx = .2, rely = .5)
    CTkButton(master = addGame, text = "ENTER", command = getWebPage(game, chrome_options)).place(relx = .2, rely = .7)

def newTrophy(root):
    return

def connect(db, dir):
    db_path = os.path.join(dir, db)
    conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + db_path)
    database = conn.cursor()
    print("Connection opened")
    return database

def getWebPage(input, chrome_options):
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