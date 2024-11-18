import sys
import re
from customtkinter import *
import pyodbc
import hashlib
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from tkinter import StringVar, Canvas, Scrollbar


# Global variables for database and chrome options
db = 'gamedata.accdb'  # Database file name
dir = sys.path[0]  # Current directory of the program
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Uncomment to run Chrome in headless mode (background)

# Main window that starts the program
def main(root):
    # Clear the window before adding new content
    for widget in root.winfo_children():
        widget.destroy()

    # Main Menu Buttons
    CTkButton(master=root, text="Initialize", command=lambda: create()).place(relx=.01, rely=.1)
    CTkButton(master=root, text="Add new Trophy").place(relx=.75, rely=.1)
    CTkButton(master=root, text="Add new game", command=lambda: newGame(root)).place(relx=.4, rely=.1)
    CTkButton(master=root, text="View Games", command=lambda: gameList(root)).pack(pady=10)

def getTitle():
    database = connect()
    try:
        database.execute('SELECT title FROM game ORDER BY title ASC')
        games = database.fetchall()
        return [game[0] for game in games]

    except Exception as e:
        print("Error retrieving titles:", e)
        return []
        
    finally:
        database.close()  # Close the connection after use

# Function to clear and change the content of the window to display the selected game
def changeWindow(root, game):
     # Clear the window before adding new content
    for widget in root.winfo_children():
        widget.destroy()

    label = CTkLabel(root, text=f"Selected Game: {game}", font=("Arial", 18))
    label.pack(pady=20)

    # Display the trophies for this game with a scrollbar
    frame = CTkFrame(root)
    frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Create a canvas to make the trophy list scrollable
    canvas = Canvas(frame)
    canvas.pack(side="left", fill="both", expand=True)

    # Create a scrollbar linked to the canvas
    scrollbar = Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Create a frame inside the canvas to hold the trophy labels
    trophy_frame = CTkFrame(canvas)
    canvas.create_window((0, 0), window=trophy_frame, anchor="nw")

    # Here, you would retrieve the trophies for the selected game
    # Assuming `getTrophies` fetches the list of trophies from the database
    trophies = getTrophiesList(game)

    # Add a label for each trophy
    for trophy in trophies:
        trophyText = f"{trophy[1]} - {'Obtained' if trophy[4] else 'Not Obtained'}"
        trophyLabel = CTkLabel(master=trophy_frame, text=trophyText)
        trophyLabel.pack(pady=5)

    # Update the scroll region to fit all trophies
    trophy_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    # Back to Game List Button
    backBtn = CTkButton(master=root, text="Back to Game List", command=lambda: gameList(root))
    backBtn.place(relx=1.0, rely=0.0, anchor="ne")

    deleteBtn = CTkButton(master=root, text="Delete Game", command=lambda: deleteData(game))
    deleteBtn.pack(anchor="ne", padx=10, pady=10)

# Display the list of games
def gameList(root):
     # Clear the window before adding new content
    for widget in root.winfo_children():
        widget.destroy()

    # Create a frame that will hold the list and the scrollbar
    frame = CTkFrame(root)
    frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Create a canvas to make the frame scrollable
    canvas = Canvas(frame)
    canvas.pack(side="left", fill="both", expand=True)

    # Create a scrollbar linked to the canvas
    scrollbar = Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Create a frame inside the canvas to hold the buttons
    button_frame = CTkFrame(canvas)
    canvas.create_window((0, 0), window=button_frame, anchor="nw")

    # Retrieve the game titles from the database
    titles = getTitle()

    # Add a button for each game title
    for game in titles:
        gameBtn = CTkButton(master=button_frame, text=game, command=lambda game=game: changeWindow(root, game))
        gameBtn.pack(pady=5)

    # Update the scroll region to fit all buttons
    button_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    # Back to Main Menu Button
    backBtn = CTkButton(master=root, text="Back to Main Menu", command=lambda: main(root))
    backBtn.place(relx=1.0, rely=0.0, anchor="ne")

def getTrophiesList(game):
    database = connect()

    try:
        database.execute('SELECT trophyID, title, description, rarity, obtained FROM trophies WHERE game = ?', (game,))
        trophies = database.fetchall()
        return trophies

    except Exception as e:
        print("Error", e)
        return []

    finally:
        database.close()
    

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

        database.execute('''
            CREATE TABLE images (
                imageID AUTOINCREMENT PRIMARY KEY,
                trophyID INTEGER,
                gameID INTEGER,
                FOREIGN KEY (trophyID) REFERENCES trophies(trophyID),
                FOREIGN KEY (gameID) REFERENCES game(gameID)
            )
        ''')
        print("Table 'images' created successfully.")
    
    except Exception as e:
        print("Error creating tables:", e)
    
    # Commit changes to the database and close the connection
    database.commit()
    database.close()

#Delete data from the database (functionality not implemented yet)
def deleteData(game):
    database = connect()

    print(game)

    database.execute('DELETE FROM trophies WHERE game = ?', (game,))
    database.execute('DELETE FROM game WHERE title = ?', (game,))

    database.commit()
    database.close()

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

    game = game.lower()
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

    game = game.lower()
    database = connect()

    try:
        # Debugging: Print the raw data for title and game
        print(f"Checking trophy existence: Title: '{name}', Game: '{game}'")

        # Check if the combination of 'game' and 'title' already exists
        existsTrophy = database.execute('SELECT COUNT(*) FROM trophies WHERE title = ? AND game = ?', (name, game))
        existsTrophy = database.fetchone()[0]  # Fetch the count from the query result

        # Debugging: Print the result of the query
        print(f"Exists Trophy: {existsTrophy}")

        if existsTrophy == 0:
            # Retrieve the gameID for the specified game
            gameID = database.execute('SELECT gameID FROM game WHERE title = ?', (game,)).fetchone()
            
            if gameID:
                gameID = gameID[0]  # Extract gameID
                print(f"GameID for '{game}': {gameID}")

                # SQL query to insert a new trophy into the 'trophies' table
                sql = '''
                    INSERT INTO trophies (gameID, game, title, description, rarity, obtained, image)
                    VALUES (?, ?, ?, ?, ?, ?)
                '''
                database.execute(sql, (gameID, game, name, description, rarity, False))  # Insert values for the trophy
                print(f"Inserted trophy: {name} into database.")

                database.commit()
                database.close()
            else:
                print(f"GameID for '{game}' not found in the database.")
        else:
            print(f"Trophy '{name}' for game '{game}' already exists in the database.")

    except Exception as e:
        print(f"Error while checking or adding trophy: {e}")

def addImage(game, trophy, imgBin):
    database = connect()

    gameID = database.execute("SELECT gameID FROM game WHERE title = ?", (game,))
    trophyID = database.execute("SELECT trophyID FROM trophies WHERE title = ?", (trophy,))

    try:
        database.execute(('''
                INSERT INTO images (trophyID, gameID, image) 
                VALUES (?, ?, ?)
            ''', (trophyID, gameID, imgBin)))

        print(game, trophy, imgBin)
        #database.commit()
    except Exception as e:
        print ("Error", e)

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
    #database.commit()
    database.close()

def convertBinary(imgPath):
    with open(imgPath, 'rb') as f:
        return f.read

def downloadImages(imageUrl, path):
    try:
        response = requests.get(imageUrl)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            print(f"Image saved at {path}")
        
        else:
            print(f"Failed to download image {imageUrl}")

    except Exception as e:
        print(f"Error failed to download image {imageUrl}", e)

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
        all_trophy_elements = driver.find_elements(By.XPATH, "//ul[contains(@class, 'achilist')]/li[contains(@class, 'achilist__item')]")
        
        print(f"Found {len(all_trophy_elements)} trophies.")

        # Loop through each trophy element from both sections
        for trophyElement in all_trophy_elements:
            # Extract the trophy title

            title = "No title found"
            description = "No description found"
            rarity = "Unknown"
            trophyImages = []
        
            try:
                title_element = trophyElement.find_element(By.XPATH, ".//div[contains(@class, 'achilist__header')]//h4[contains(@class, 'achilist__title')]")
                title = title_element.text
                print(f"Trophy: {title}")
            except Exception as e:
                print("Error while scraping trophy title:", e)

            # Extract the description from the <p> tag inside achilist__data
            description = "No description found"
            try:
                description_element = trophyElement.find_element(By.XPATH, ".//div[@class='achilist__data']//p[not(ancestor::div[@class='achilist__header'])]")
                description = description_element.text
                print(f"Description: {description}")
            except Exception as e:
                print("Error while scraping description:", e)

            # Get the rarity image
            rarity = "Unknown"
            try:
                rarity_image = trophyElement.find_element(By.XPATH, ".//div[@class='achilist__value']//img")
                rarity_src = rarity_image.get_attribute("src")
                rarity = getRarity(rarity_src)  # Assuming you have a function to determine rarity from the image source
                print(f"Rarity: {rarity}")
            except Exception as e:
                print("Error while scraping rarity:", e)

            try:
                imageElement = trophyElement.find_element(By.XPATH, "/html/body/div[2]/div/div[3]/div/div[1]/section[1]/div[2]/div/ul[1]/li[3]/div[1]/img")
                imageUrl = imageElement.get_attribute("src")
                trophyImages.append(imageUrl)
                print (trophyImages)

                for idx, trophyImage in enumerate(trophyImages, start = 1):

                    hashedUrl = hashlib.md5(trophyImage.encode()).hexdigest()  # Generate a hash of the URL to ensure uniqueness
                    path = f"images/{hashedUrl}.jpg"

                    downloadImages(trophyImage, path)
                    imgBin = convertBinary*(path)

                    addImage(game, title, imgBin = imgBin)
            except Exception as e:
                print("Error", e)

            # Optionally, add trophy data to the database
            #try:
                #addTrophyData(game.get(), title, description, rarity)
            #except Exception as e:
                #print(f"Error while adding trophy data: {e}")

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

def runGui():
    # Initialize the root window
    root = CTk(className="Trophy Tracker")
    root.geometry("590x500")
    root.title("Trophy Tracker")

    # Set the appearance mode for the application (dark mode in this case)
    set_appearance_mode("dark")

    # Call the main menu to set up the initial view
    main(root)

    # Run the Tkinter main loop to display the window
    root.mainloop()

if __name__ == '__main__':
    runGui()