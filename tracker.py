import sys
import re
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

#global variables 
db = 'gamedata.accdb'
dir = sys.path[0]



def main():
    chrome_options = Options()
    #chrome_options.add_argument("--headless")  # Run browser in background 

    root = CTk(className="Trophy Tracker") 
    root.geometry("590x500")
    root.title("Trophy Tracker")

    set_appearance_mode("dark")

    CTkButton(master = root, text = "Initialize", command = lambda: create()).place(relx = .01, rely = .5)
    CTkButton(master = root, text = "Add new Trophy").place(relx = .7, rely = .5)
    CTkButton(master = root, text = "Add new game", command = lambda: newGame(root, chrome_options)).place(relx = .4, rely = .5)

    root.mainloop()

def create():

    # Connect to the Access database
    database = connect()
    
    # Execute SQL to create a table
    try:
        #SQL to create the game table for storing game data
        database.execute('CREATE TABLE game (gameID AUTOINCREMENT PRIMARY KEY, title TEXT NOT NULL, numoftrophies INTEGER, earned INTEGER, platinum YESNO)')
        print("Table 'game' created successfully.")

        #SQL to create the table for trophy data. gameID used as foreign key
        database.execute('CREATE TABLE trophies (trophyID AUTOINCREMENT PRIMARY KEY, gameID INTEGER, game TEXT NOT NULL, title TEXT NOT NULL, description MEMO NOT NULL, rarity TEXT NOT NULL, obtained YESNO, FOREIGN KEY (gameID) REFERENCES game(gameID))')
        print("Table 'trophies' created successfully.")

    except Exception as e:
        print("Error creating tables:", e)
    
    # Commit changes and close the database connection
    database.commit()
    database.close()

#Function to delete all data in the database 
def deleteData():
    return

#Adds new game to the database
def newGame(root, chrome_options):
    game = StringVar()

    addGame = CTkToplevel(root)
    addGame.title("Add New Game")
    addGame.geometry("400x300")

    entry = CTkEntry(master = addGame, placeholder_text= "What is the new game?", textvariable = game).place(relx = .2, rely = .5)
    btn = CTkButton(master = addGame, text = "ENTER", command = lambda: getWebPage(game, chrome_options)).place(relx = .2, rely = .7)

#Updates a trophies status to being obtained
def newTrophy(root):
    return

#Connects to the Access database
def connect():
    db_path = os.path.join(dir, db)
    conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + db_path)
    database = conn.cursor()
    print("Connection opened")
    return database

#Adds the required information about the game to the game table
def addGameData(game, trophynum):

    print(game, trophynum)
    database = connect()

    sql = '''
            INSERT INTO trophies (title, numoftrophies, platinum)
            VALUES (?, ?, ?)
        '''
    
    database.execute(sql, (game, trophynum, False))

    #database.commit()
    database.close()

#Adds the required information about the trophies to the trophy table
def addTrophyData(game, name, description, rarity):
    print (game, name, description, rarity)
    database = connect()

    sql = '''
            INSERT INTO game (game, title, description, rarity, obtained)
            VALUES (?, ?, ?, ?, ?)
        '''
    
    database.execute(sql, (name, game, description, rarity, False))

    #database.commit()
    database.close()

#Scrapes the required information from the webpage
def getWebPage(game, chrome_options):

    #Formatting input to work with the URL
    gameUrl = game.get().replace(" ", "-").lower()
    print(f"Game Name: {gameUrl}")

    #URL for the webpage with all trophy data
    url =  f"https://www.playstationtrophies.org/game/{gameUrl}/trophies/"

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        time.sleep(3)

        button = driver.find_element(By.XPATH, "/html/body/div[5]/div[2]/div[2]/div[2]/div[2]/button[1]")
        button.click()
        print("Button clicked")

        time.sleep(3)

        try:
            trophynum = driver.find_element(By.CLASS_NAME, 'h-3')
            trophynumText = trophynum.text

            trophyCount = re.search(r"(\d+)\s+trophies", trophynumText)

            addGameData(game, trophyCount)
        
        except Exception as e:
            print("Error", e)

        titles = driver.find_elements(By.CLASS_NAME, 'achilist__header')

        for title in titles:
            print("Title Found", title.text)
    
    except Exception as e:
        print("Error", e)

    driver.quit()

if __name__ == '__main__':
    main()