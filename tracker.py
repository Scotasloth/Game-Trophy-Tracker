import sys
from customtkinter import *
import pyodbc
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
from tkinter import StringVar
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

    CTkButton(master = root, text = "Initialize", command = lambda: create(program_directory)).place(relx = .01, rely = .5)
    CTkButton(master = root, text = "Add new Trophy").place(relx = .7, rely = .5)
    CTkButton(master = root, text = "Add new game", command = lambda: newGame(root, chrome_options)).place(relx = .4, rely = .5)

    root.mainloop()

def create(dir):
    db_name = 'gamedata.accdb'

    # Connect to the Access database
    database = connect(db_name, dir)
    
    # Execute SQL to create a table
    try:
        database.execute('CREATE TABLE game (gameID AUTOINCREMENT PRIMARY KEY, title TEXT NOT NULL, numoftrophies INTEGER, platinum YESNO)')
        print("Table 'game' created successfully.")

        database.execute('CREATE TABLE trophies (trophyID AUTOINCREMENT PRIMARY KEY, game TEXT NOT NULL, title TEXT NOT NULL, description MEMO NOT NULL, rarity TEXT NOT NULL, obtained YESNO)')
        print("Table 'trophies' created successfully.")

    except Exception as e:
        print("Error creating tables:", e)
    
    # Close the database connection
    database.commit()
    database.close()

def deleteData():
    return

def newGame(root, chrome_options):
    game = StringVar()

    addGame = CTkToplevel(root)
    addGame.title("Add New Game")
    addGame.geometry("400x300")

    entry = CTkEntry(master = addGame, placeholder_text= "What is the new game?", textvariable = game).place(relx = .2, rely = .5)
    btn = CTkButton(master = addGame, text = "ENTER", command = lambda: getWebPage(game, chrome_options)).place(relx = .2, rely = .7)

def newTrophy(root):
    return

def connect(db, dir):
    db_path = os.path.join(dir, db)
    conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + db_path)
    database = conn.cursor()
    print("Connection opened")
    return database

def getWebPage(game, chrome_options):
    url = ("https://www.playstationtrophies.org/game/", game, "/trophies/")

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