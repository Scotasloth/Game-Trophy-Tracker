import sys
import re
from customtkinter import *
import pyodbc
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from tkinter import StringVar


# Global variables for database and chrome options
db = 'gamedata.accdb'  # Database file name
dir = sys.path[0]  # Current directory of the program
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Uncomment to run Chrome in headless mode (background)

def main():
    # Create the main window for the program using customtkinter
    root = CTk(className="Trophy Tracker") 
    root.geometry("590x500")
    root.title("Trophy Tracker")

    # Set the appearance mode for the application (dark mode in this case)
    set_appearance_mode("dark")

    # Define buttons for various functionalities
    CTkButton(master=root, text="Initialize", command=lambda: create()).place(relx=.01, rely=.5)
    CTkButton(master=root, text="Add new Trophy").place(relx=.7, rely=.5)
    CTkButton(master=root, text="Add new game", command=lambda: newGame(root)).place(relx=.4, rely=.5)

    # Run the main loop to display the GUI
    root.mainloop()

def create():
    """Create the required database tables if they don't exist."""
    database = connect()  # Connect to the database

    try:
        # SQL to create the game table for storing game data
        database.execute('''
            CREATE TABLE game (
                gameID AUTOINCREMENT PRIMARY KEY,
                title TEXT NOT NULL,
                numoftrophies INTEGER,
                earned INTEGER,
                platinum YESNO
            )
        ''')
        print("Table 'game' created successfully.")

        # SQL to create the trophies table, referencing gameID as a foreign key
        database.execute('''
            CREATE TABLE trophies (
                trophyID AUTOINCREMENT PRIMARY KEY,
                gameID INTEGER,
                game TEXT NOT NULL,
                title TEXT NOT NULL,
                description MEMO NOT NULL,
                rarity TEXT NOT NULL,
                obtained YESNO,
                FOREIGN KEY (gameID) REFERENCES game(gameID)
            )
        ''')
        print("Table 'trophies' created successfully.")
    
    except Exception as e:
        print("Error creating tables:", e)
    
    # Commit changes to the database and close the connection
    database.commit()
    database.close()

#Delete all data from the database (functionality not implemented yet)
def deleteData():
    return

#Open a new window to input a new game and scrape its data
def newGame(root):
    game = StringVar()  # Variable to hold the game title

    # Create a new popup window for adding a game
    addGame = CTkToplevel(root)
    addGame.title("Add New Game")
    addGame.geometry("400x300")

    # Add a text entry field and a button for entering the game title
    entry = CTkEntry(master=addGame, placeholder_text="What is the new game?", textvariable=game).place(relx=.2, rely=.5)
    btn = CTkButton(master=addGame, text="ENTER", command=lambda: getWebPage(game, chrome_options)).place(relx=.2, rely=.7)

def connect():
    """Connect to the Access database and return a database cursor."""
    db_path = os.path.join(dir, db)  # Path to the database file
    conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + db_path)  # ODBC connection string
    database = conn.cursor()  # Create a cursor for executing SQL queries
    print("Connection opened")
    return database

#Add a new game to the game table
def addGameData(game, trophynum):
    print(game, trophynum)
    database = connect()

    exists = database.execute('SELECT COUNT(*) FROM game WHERE title = ?', (game))

    exists = database.fetchone()[0]  # Fetch the count from the query result

    if exists == 0:
        # Game does not exist, proceed to insert it
        print(f"Game '{game}' does not exist in the database. Inserting...")
        sql = '''
            INSERT INTO game (title, numoftrophies, earned, platinum)
            VALUES (?, ?, ?, ?)
        '''
        database.execute(sql, (game, trophynum, 0, False))  # Insert game data into the database
        print(f"Game '{game}' added to the database.")
    else:
        # Game already exists in the database
        print(f"Game '{game}' already exists in the database.")

    # Commit changes to the database and close the connection
    database.commit()
    database.close()

#Add a new trophy to the trophies table
def addTrophyData(game, name, description, rarity):
    print(game, name, description, rarity)
    database = connect()

    # Retrieve the gameID for the specified game
    gameID = database.execute('SELECT gameID FROM game WHERE title = ?', (game,)).fetchone()[0]
    print(f"GameID for '{game}': {gameID}")

    # SQL query to insert a new trophy into the 'trophies' table
    sql = '''
        INSERT INTO trophies (gameID, game, title, description, rarity, obtained)
        VALUES (?, ?, ?, ?, ?, ?)
    '''
    database.execute(sql, (gameID, game, name, description, rarity, False))  # Insert values for the trophy

    # Commit changes to the database and close the connection
    database.commit()
    database.close()

#Update the status of a trophy when it's earned
def updateTrophy(trophy):
    database = connect()

    # Retrieve the gameID for the trophy
    gameID = database.execute('SELECT gameID FROM trophies WHERE title = ?', (trophy,)).fetchone()[0]

    # Retrieve the current number of earned trophies for the game
    earnedVal = database.execute('SELECT earned FROM game WHERE gameID = ?', (gameID,)).fetchone()[0]
    earnedVal += 1  # Increment the earned value
    print(f"Updated earned value: {earnedVal}")

    # Update the 'earned' value in the 'game' table
    sqlGame = 'UPDATE game SET earned = ? WHERE gameID = ?'
    database.execute(sqlGame, (earnedVal, gameID))

    # Update the 'obtained' value in the 'trophies' table
    sqlTrophy = 'UPDATE trophies SET obtained = ? WHERE title = ?'
    database.execute(sqlTrophy, (True, trophy))

    # Commit changes to the database and close the connection
    database.commit()
    database.close()

#Scrape the webpage to get the game data and trophy information.
def getWebPage(game, chrome_options):
    
    # Format the game name to work with the URL
    gameUrl = game.get().replace(" ", "-").lower()
    print(f"Game Name: {gameUrl}")

    # Construct the URL for the game's trophy page
    url = f"https://www.playstationtrophies.org/game/{gameUrl}/trophies/"

    # Set up the Selenium WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Open the webpage
        driver.get(url)
        time.sleep(3)  # Wait for the page to load

        # Click the button (if exists)
        try:
            button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div[2]/div[2]/div[2]/div[2]/button[1]")))
            button.click()
            print("Button clicked")
            time.sleep(3)

        except Exception as e:
            print("Error clicking button:", e)

        # Scrape the trophy count from the correct <h3> element
        try:
            # Find all <h3> tags with the class 'h-3'
            h3Elements = driver.find_elements(By.CLASS_NAME, 'h-3')
            
            if len(h3Elements) > 1:
                trophynumText = h3Elements[1].text  # Get the second <h3> element
                print("Trophy Count Text:", trophynumText)

                # Extract the number of trophies using regex
                trophyCountMatch = re.search(r"(\d+)\s+trophies", trophynumText)
                
                if trophyCountMatch:
                    trophyCount = int(trophyCountMatch.group(1))  # Convert to integer
                    print(f"Trophy Count: {trophyCount}")

                    #addGameData(game.get(), trophyCount)  # Pass the trophy count as an integer
                else:
                    print("Trophy count not found in the text:", trophynumText)
            else:
                print("Not enough <h3> tags found.")
        
        except Exception as e:
            print("Error while scraping trophy data:", e)

        # Scrape trophy titles (assuming a class of 'achilist__header')
        try:
            # Find all divs with the class 'achlist_data' which contain trophies and descriptions
            achilist_data_elements = driver.find_elements(By.XPATH, "/html/body/div[2]/div/div[3]/div/div[1]/section[1]/div[2]/div/ul[1]/li/div[2]")
            print("Found achlist_data elements:", len(achilist_data_elements))  # Debugging line

            if achilist_data_elements:
                for achilist_data_element in achilist_data_elements:
                    # Print HTML content of achlist_data element for debugging

                    # Find the trophy title in the current achlist_data div
                    try:
                        title_element = achilist_data_element.find_element(By.CLASS_NAME, "achilist__header")
                        title = title_element.text
                        print(f"Trophy: {title}")
                    except Exception as e:
                        print("Error while scraping trophy title:", e)

                    # Find the description in the same achlist_data div
                    try:
                        # Look for the description in the sibling or child div
                        description = achilist_data_element.find_element(By.XPATH, ".//p[not(ancestor::div[@class='achilist__header'])]").text
                        print(f"Description: {description}")
                    
                    except Exception as e:
                        print("Error while scraping description:", e)

                    # Scrape rarity image (relative to each trophy)
                    try:
                        rarity_image = achilist_data_element.find_element(By.XPATH, ".//span//img")
                        rarity_src = rarity_image.get_attribute("src")
                        rarity = getRarity(rarity_src)  # Function to map image src to rarity text
                        print(f"Rarity: {rarity}")
                    except Exception as e:
                        print("Error while scraping rarity:", e)

                    # Optionally, add trophy data to the database
                    # addTrophyData(game.get(), title, description, rarity)

            else:
                print("No trophies found on the page.")

        except Exception as e:
            print("Error while scraping trophies:", e)

    except Exception as e:
        print("Error while scraping webpage:", e)

    finally:
        driver.quit()
#Reads img src to know what rarity a trophy is
def getRarity(imgSrc):
    if "trophy_platinum" in imgSrc:
        return "Platinum"
    elif "trophy_gold" in imgSrc:
        return "Gold"
    elif "trophy_silver" in imgSrc:
        return "Silver"
    elif "trophy_bronze" in imgSrc:
        return "Bronze"
    else:
        return "Unknown"
    
if __name__ == '__main__':
    main()