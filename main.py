import sys
from customtkinter import *
from customtkinter import CTkImage  # Import CTkImage
from tkinter import StringVar, Canvas, Scrollbar
from PIL import Image
import pyodbc
import connect as conn
import scraperps as ps
import scraperxbox as xb
import scraperpc as pc
from PIL import ImageEnhance
import pygame


# Global variables for database and chrome options
db = 'gamedata.accdb'  # Database file name
dir = sys.path[0]  # Current directory of the program
database = conn.connect()

pygame.mixer.init()
trophyObtainedEffect = pygame.mixer.Sound(f'{dir}/sounds/trophyObtained.mp3')

# Main window that starts the program
def main(root):
    # Clear the window before adding new content
    for widget in root.winfo_children():
        widget.destroy()

    # Main Menu Buttons
    CTkButton(master=root, text="Initialize", command=lambda: create()).place(relx=.01, rely=.1)
    CTkButton(master=root, text="Add new game", command=lambda: newGame(root)).place(relx=.4, rely=.1)
    CTkButton(master=root, text="View Games", command=lambda: gameList(root)).place(relx=.75, rely=.1)

    recentGame1 = updateRecent(1)
    recentGame2 = updateRecent(2)
    recentGame3 = updateRecent(3)
    recentGame4 = updateRecent(4)
    recentGame5 = updateRecent(5)

    CTkLabel(master = root, text = "RECENT:", font=("Arial", 25)).place(relx=.01, rely=.2)

    try:
        CTkLabel(master = root, text = f"{recentGame1[4].upper()} - {recentGame1[3]}").place(relx=.01, rely=.3)

    except Exception as e:
        print(f"Error no data in recent: {e}")

    try:
        CTkLabel(master = root, text = f"{recentGame2[4].upper()} - {recentGame2[3]}").place(relx=.01, rely=.4)

    except Exception as e:
        print(f"Error no data in recent: {e}")

    try:
        CTkLabel(master = root, text = f"{recentGame3[4].upper()} - {recentGame3[3]}").place(relx=.01, rely=.5)

    except Exception as e:
        print(f"Error no data in recent: {e}")

    try:
        CTkLabel(master = root, text = f"{recentGame4[4].upper()} - {recentGame4[3]}").place(relx=.01, rely=.6)

    except Exception as e:
        print(f"Error no data in recent: {e}")

    try:
        CTkLabel(master = root, text = f"{recentGame5[4].upper()} - {recentGame5[3]}").place(relx=.01, rely=.7)

    except Exception as e:
        print(f"Error no data in recent: {e}")

def updateRecent(val):
    recent = 0

    if val == 1:
        try:
            recent = database.execute("SELECT * FROM recent WHERE recentID = ?", (1,)).fetchone()

        except Exception as e:
            print(f"Error with getting recent {e}")

    elif val == 2:
        try:
            recent = database.execute("SELECT * FROM recent WHERE recentID = ?", (2,)).fetchone()
    
        except Exception as e:
            print(f"Error with getting recent {e}")

    elif val == 3:
        try:
            recent = database.execute("SELECT * FROM recent WHERE recentID = ?", (3,)).fetchone()
    
        except Exception as e:
            print(f"Error with getting recent {e}")

    elif val == 4:
        try:
            recent = database.execute("SELECT * FROM recent WHERE recentID = ?", (4,)).fetchone()
    
        except Exception as e:
            print(f"Error with getting recent {e}")

    elif val == 5:
        try:
            recent = database.execute("SELECT * FROM recent WHERE recentID = ?", (5,)).fetchone()
    
        except Exception as e:
            print(f"Error with getting recent {e}")

    return recent

def playSound():
    trophyObtainedEffect.play()

def addRecent(trophy):
    gameID = database.execute("SELECT gameID FROM trophies WHERE trophyID = ?", (trophy[0],)).fetchone()
    platform = database.execute("SELECT platform FROM trophies WHERE trophyID = ?", (trophy[0],)).fetchone()
    game = database.execute("SELECT game FROM trophies WHERE trophyID = ?", (trophy[0],)).fetchone()

    try:
        # Step 1: Check if the table is empty. If it is, no need to update the recentID.
        count =  database.execute("SELECT COUNT(*) FROM recent").fetchone()[0]
        

        if count > 0:
            # If there are existing rows, increment the recentID for all existing rows
            if count > 0:
                rows = database.execute("SELECT recentID FROM recent ORDER BY recentID DESC").fetchall()

                # Step 3: Manually update recentID in descending order
                for i, row in enumerate(rows):

                    # Calculate the new recentID (decrementing it by 1)
                    newRecentID = row[0] + 1

                    # Update the row with the new recentID
                    database.execute("""
                        UPDATE recent
                        SET recentID = ?
                        WHERE recentID = ?
                    """, newRecentID, row[0])
        
        # Step 2: Insert the new row with recentID = 1 (it will be the first row)
        try:
            database.execute("""
                INSERT INTO recent (recentID, gameID, trophyID, trophy, game, platform)
                VALUES (?, ?, ?, ?, ?, ?)
            """, 1, gameID[0], trophy[0], trophy[1], game[0], platform[0])
        except Exception as e:
            print(f"Error adding new data to recent: {e}")
        
        # Step 3: Ensure the table never has more than 5 rows
        if count >= 5:
            try:
                # If there are 5 or more rows, delete the row with the highest recentID (most recent)
                database.execute("""
                    DELETE FROM recent
                    WHERE recentID > 5
                """)
            except Exception as e:
                print(f"Error deleting excess rows: {e}")

        # Commit the transaction
        database.commit()

    except Exception as e:
        print(f"Unexpected error: {e}")

def getTitle():
    try:
        database.execute('SELECT gameID FROM game ORDER BY title ASC')
        games = database.fetchall()
        return [game[0] for game in games]
    
    except Exception as e:
        print("Error retrieving titles:", e)
        return []

# Function to clear and change the content of the window to display the selected game
def changeWindow(root, game, title, platform):
    # Clear the window before adding new content
    for widget in root.winfo_children():
        widget.destroy()

    # Retrieve the max number of trophies for the selected game
    maxTrophies = database.execute("SELECT numoftrophies FROM game WHERE gameID = ? AND platform = ?", (game, platform,)).fetchone()
    currentTrophies = database.execute("SELECT earned FROM game WHERE gameID = ? AND platform = ?", (game, platform,)).fetchone()

    maxTrophiesVal = maxTrophies[0] if maxTrophies else 0
    currentTrophiesVal = currentTrophies[0] if currentTrophies else 0

    # Label for showing current trophies earned
    trophyLabelTop = CTkLabel(root, text=f"Selected Game: {title} {currentTrophiesVal}/{maxTrophiesVal}", font=("Arial", 18))
    trophyLabelTop.pack(pady=20)

    # Display the trophies for this game with a scrollbar
    frame = CTkFrame(root)
    frame.pack(fill='both', expand=True, padx=10, pady=10)

    canvas = Canvas(frame)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)

    trophyFrame = CTkFrame(canvas)
    canvas.create_window((0, 0), window=trophyFrame, anchor="nw")

    trophies = getTrophiesList(game)

    for index, trophy in enumerate(trophies):
        print("THIS IS IN CHANGEWINDOW,", index)
        trophyText = f"{trophy[1]} - {'Obtained' if trophy[4] else 'Not Obtained'}"
        
        trophyId = trophy[0]
        database.execute('SELECT path FROM images WHERE trophyID = ?', (trophyId,))
        image = database.fetchone()
        rarity = database.execute("SELECT rarity FROM trophies WHERE trophyID = ?", (trophyId,)).fetchone()[0]
        
        iconsDir = os.path.join(dir, "icons")
        imageFilename = image[0] if image else "default_image.jpg"
        imagePath = os.path.join(iconsDir, imageFilename)
        rarityImgPath = checkRarity(rarity)
        imgRPath = os.path.join(iconsDir, rarityImgPath)

        try:
            img = Image.open(imagePath)
            if not trophy[4]:  # If the trophy is not obtained
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.0)  # Make the image grayscale

            img = img.resize((50, 50))
            imgTk = CTkImage(img, size=(50, 50))

        except Exception as e:
            imgTk = None
            print(f"Error loading image for trophy {trophy[1]}: {e}")

        # Create a frame to hold the image and the text
        trophyFrameInner = CTkFrame(trophyFrame)
        trophyFrameInner.pack(pady=5, anchor="w", fill="x", padx=10)

        # Display the trophy image
        if imgTk:
            imageLabel = CTkLabel(master=trophyFrameInner, image=imgTk, text="") 
            imageLabel.image = imgTk  # Ensure the image is retained
            imageLabel.pack(side="top", padx=10, pady=0)

            if not trophy[4]:  # Trophy not obtained, make image clickable
                imageLabel.bind("<Button-1>", lambda event, t=trophy, label=imageLabel, trophyLabelTop=trophyLabelTop: onImageClick(t, label, trophyLabelTop))

        # Process the rarity image
        try:
            imgR = Image.open(imgRPath)
            imgR = imgR.resize((50, 50))
            imgRTk = CTkImage(imgR, size=(50, 50))

        except Exception as e:
            imgRTk = None
            print(f"Error displaying trophy rarity: {e}")

        # Display the rarity image if it's successfully loaded
        if imgRTk:
            rarityLabel = CTkLabel(master=trophyFrameInner, image=imgRTk, text="")
            rarityLabel.image = imgRTk  # Retain the image reference
            imageLabel.pack(side="top", padx=10, pady=0)

        # Display the trophy description
        trophyLabel = CTkLabel(master=trophyFrameInner, text=trophyText)
        trophyLabel.pack(side="top", padx=10, pady=2)  # Add padding between labels

        # Create the description label (this is the description or additional information)
        descLabel = CTkLabel(master=trophyFrameInner, text=trophy[2])
        descLabel.pack(side="top", padx=10, pady=2)

    trophyFrame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    # Back button and delete button
    backBtn = CTkButton(master=root, text="Back to Game List", command=lambda: gameList(root))
    backBtn.place(relx=1.0, rely=0.0, anchor="ne")

    deleteBtn = CTkButton(master=root, text="Delete Game", command=lambda: deleteData(game))
    deleteBtn.pack(anchor="ne", padx=10, pady=10)

# Function to handle image click and mark trophy as obtained
def onImageClick(trophy, label, trophyLabelTop):
    playSound()
    
    try:
        # Step 1: Update the trophy status in the database
        database.execute("UPDATE trophies SET obtained = ? WHERE trophyID = ?", (True, trophy[0]))  # Set 'obtained' to True
        database.commit()

        #trophyLabel.configure(text=f"{trophy[1]} - Obtained")

        # Step 2: Update the trophy image to full color
        imagePath = getImagePathForTrophy(trophy)
        img = Image.open(imagePath)
        img = img.resize((50, 50))
        imgTk = CTkImage(img, size=(50, 50))
        label.configure(image=imgTk)
        label.image = imgTk  # Keep a reference to avoid garbage collection

        # Step 3: Update the earned trophy count for the game
        updateTrophy(trophy, trophyLabelTop)

    except Exception as e:
        print(f"Error updating trophy status: {e}")
    
    addRecent(trophy)

# Function to get the image path for the trophy
def getImagePathForTrophy(trophy):
    trophyId = trophy[0]
    database.execute('SELECT path FROM images WHERE trophyID = ?', (trophyId,))
    image = database.fetchone()
    iconsDir = os.path.join(dir, "icons")
    return os.path.join(iconsDir, image[0]) if image else os.path.join(iconsDir, "default_image.jpg")

def checkRarity(rarity):
    try:
        # Determine the image based on rarity
        if rarity == "Platinum":
            return "psplat.png"
        elif rarity == "Gold":
            return "psgold.png"
        elif rarity == "Silver":
            return "pssilver.png"
        elif rarity == "Bronze":
            return "psbronze.png"
        else:
            return "default_image.jpg"

    except pyodbc.Error as e:
        print(f"Error checking rarity: {e}")
        return "default_image.jpg"

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

        plat = database.execute("SELECT platinum FROM game WHERE gameID = ?", (game,)).fetchone()[0]
        platform = database.execute("SELECT platform FROM game WHERE gameID = ?", (game,)).fetchone()
        gameName = database.execute("SELECT title FROM game WHERE gameID = ?", (game,)).fetchone()

        platform = platform[0] if platform else "Unknown"  # Default to "Unknown" if no platform is found
        gameName = gameName[0] if gameName else "Unknown Game"  # Default to "Unknown Game" if no game name is found

        if plat == True:
            gameBtn = CTkButton(master=button_frame, fg_color="gold", text_color="black", text=(f"{gameName.upper()} - {platform.upper()}"), command=lambda game=game, gameName=gameName, platform=platform: changeWindow(root, game, gameName, platform))
            gameBtn.pack(pady=5)
        
        elif platform == "xbox":
            gameBtn = CTkButton(master=button_frame, fg_color="green", hover_color="#006400", text=(f"{gameName.upper()} - {platform.upper()}"), command=lambda game=game, gameName=gameName, platform=platform: changeWindow(root, game, gameName, platform))
            gameBtn.pack(pady=5)
        
        else:
            gameBtn = CTkButton(master=button_frame, text=(f"{gameName.upper()} - {platform.upper()}"), command=lambda game=game, gameName=gameName, platform=platform: changeWindow(root, game, gameName, platform))
            gameBtn.pack(pady=5)

        earned = database.execute("SELECT earned FROM game WHERE gameID = ?", (game,)).fetchone()[0]
        total = database.execute("SELECT numoftrophies FROM game WHERE gameID = ?", (game,)).fetchone()[0]

        gameLbl = CTkLabel(master = button_frame, text=f"{earned}/{total}")
        gameLbl.pack(pady=5)

    # Update the scroll region to fit all buttons
    button_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    # Back to Main Menu Button
    backBtn = CTkButton(master=root, text="Back to Main Menu", command=lambda: main(root))
    backBtn.place(relx=1.0, rely=0.0, anchor="ne")

def getTrophiesList(game):
    try:
        database.execute('SELECT trophyID, title, description, rarity, obtained FROM trophies WHERE gameID = ?', (game,))
        trophies = database.fetchall()
        return trophies

    except Exception as e:
        print("Error", e)
        return []

#Create the required database tables if they don't exist
def create():
    try:
        # SQL to create the game table for storing game data
        database.execute('''
            CREATE TABLE game (
                gameID AUTOINCREMENT PRIMARY KEY,
                title TEXT NOT NULL,
                platform TEXT NOT NULL,
                numoftrophies INTEGER,
                earned INTEGER,
                platinum YESNO
            )
        ''')
        print("Table 'game' created successfully.")
    
    except Exception as e:
        print(f"Error creating game table {e}")

    try:
        # SQL to create the trophies table, referencing gameID as a foreign key
        database.execute('''
            CREATE TABLE trophies (
                trophyID AUTOINCREMENT PRIMARY KEY,
                gameID INTEGER,
                game TEXT NOT NULL,
                title TEXT NOT NULL,
                description MEMO NOT NULL,
                rarity TEXT NOT NULL,
                platform TEXT NOT NULL,
                obtained YESNO,
                FOREIGN KEY (gameID) REFERENCES game(gameID)
            )
        ''')
        print("Table 'trophies' created successfully.")

    except Exception as e:
        print(f"Error creating trophies table {e}")

    try:
        database.execute('''
            CREATE TABLE images (
                imageID AUTOINCREMENT PRIMARY KEY,
                trophyID INTEGER,
                gameID INTEGER,
                platform TEXT NOT NULL,
                path TEXT NOT NULL,
                FOREIGN KEY (trophyID) REFERENCES trophies(trophyID),
                FOREIGN KEY (gameID) REFERENCES game(gameID)
            )
        ''')
        print("Table 'images' created successfully.")

        sql = '''
            INSERT INTO images (platform, path)
            VALUES (?, ?)
        '''

        database.execute(sql, ("ps", "psplat.png"))
        database.execute(sql, ("ps", "psgold.png"))
        database.execute(sql, ("ps", "pssilver.png"))
        database.execute(sql, ("ps", "psbronze.png"))
    
    except Exception as e:
        print(f"Error creating image table {e}:")

    try:
        database.execute('''
            CREATE TABLE recent (
                recentID INTEGER PRIMARY KEY,
                trophyID INTEGER,
                gameID INTEGER,
                trophy TEXT NOT NULL,
                game TEXT NOT NULL,
                platform TEXT NOT NULL,
                FOREIGN KEY (trophyID) REFERENCES trophies(trophyID),
                FOREIGN KEY (gameID) REFERENCES game(gameID)
            )
        ''')
        print("Table 'recent' created successfully.")

    except Exception as e:
        print(f"Error creating recent table: {e}")
    
    # Commit changes to the database and close the connection
    database.commit()

#Delete data from the database (functionality not implemented yet)
def deleteData(game):
    print(game)

    gameID = database.execute("SELECT gameID FROM game WHERE gameID = ?", (game,)).fetchone()
    if gameID:
        gameID = int(gameID[0])  # Ensure gameID is an integer

        #Delete entries from recent
        database.execute('DELETE FROM recent WHERE gameID = ?', (game,))

        # Delete related images
        database.execute("DELETE FROM images WHERE gameID = ?", (gameID,))

        # Delete related trophies
        database.execute('DELETE FROM trophies WHERE gameID = ?', (game,))

        # Delete the game
        database.execute('DELETE FROM game WHERE gameID = ?', (game,))

        # Commit the changes
        database.commit()

    else:
        print(f"Game '{game}' not found in the database.")

#Open a new window to input a new game and scrape its data
def newGame(root):
    game = StringVar()  # Variable to hold the game title
    platform = StringVar() # Variable for the games platform (PS, Xbox, PC/Steam)

    # Create a new popup window for adding a game
    addGame = CTkToplevel(root)
    addGame.title("Add New Game")
    addGame.geometry("400x300")

    # Add a text entry field and a button for entering the game title
    entryGame = CTkEntry(master=addGame, placeholder_text="What is the new game?", textvariable=game).place(relx=.2, rely=.5)
    entryPlatform = CTkEntry(master=addGame, placeholder_text="What platform is the game for?", textvariable=platform).place(relx=.2, rely=.7)

    btn = CTkButton(master=addGame, text="ENTER", command=lambda: choosePlatform(game, platform)).place(relx=.2, rely=.9)

def choosePlatform(game, platform):
    platform = platform.get().lower()

    if platform == "ps" or platform == "ps5" or platform == "playstation":
        ps.getWebPage(game)

    elif platform == "xbox":
        xb.getWebPage(game)
    
    elif platform == "pc" or platform == "steam":
        pc.getWebPage(game)

#Update the status of a trophy when it's earned
def updateTrophy(trophy, trophyLabel):
    try:
        # Step 1: Get the game ID for the selected game
        trophyID = trophy[0]
        gameID = database.execute("SELECT gameID FROM trophies WHERE trophyID = ?", (trophyID,)).fetchone()[0]
        game = database.execute("SELECT game FROM trophies WHERE trophyID = ?", (trophyID,)).fetchone()[0]

        # Step 2: Increment the 'earned' trophy count in the database
        earnedVal = database.execute('SELECT earned FROM game WHERE gameID = ?', (gameID,)).fetchone()[0]
        earnedVal += 1  # Increment the earned trophies count
        database.execute('UPDATE game SET earned = ? WHERE gameID = ?', (earnedVal, gameID))

        maxTrophies = database.execute("SELECT numoftrophies FROM game WHERE gameID = ?", (gameID,)).fetchone()[0]

        if earnedVal == maxTrophies:
            database.execute("""
                        UPDATE game
                        SET platinum = ?
                        WHERE gameID = ?
                    """, True, gameID)

        database.commit()

        # Step 3: Update the label to reflect the new earned count
        currentTrophies = database.execute("SELECT earned FROM game WHERE gameID = ?", (gameID,)).fetchone()[0]
        maxTrophies = database.execute("SELECT numoftrophies FROM game WHERE gameID = ?", (gameID,)).fetchone()[0]

        # Dynamically update the trophy label here
        trophyLabel.configure(text=f"Selected Game: {game} {currentTrophies}/{maxTrophies}")
        
    except Exception as e:
        print(f"Error updating game progress: {e}")


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