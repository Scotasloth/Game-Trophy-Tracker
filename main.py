import sys
from customtkinter import *
from customtkinter import CTkImage  # Import CTkImage
from tkinter import StringVar, Canvas, Scrollbar
from PIL import Image, ImageTk
import pyodbc
import connect as conn
import scraper as s


# Global variables for database and chrome options
db = 'gamedata.accdb'  # Database file name
dir = sys.path[0]  # Current directory of the program
database = conn.connect()

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
    try:
        database.execute('SELECT title FROM game ORDER BY title ASC')
        games = database.fetchall()
        return [game[0] for game in games]

    except Exception as e:
        print("Error retrieving titles:", e)
        return []

# Function to clear and change the content of the window to display the selected game
def changeWindow(root, game):
    # Clear the window before adding new content
    for widget in root.winfo_children():
        widget.destroy()

    maxTrophies = database.execute("SELECT numoftrophies FROM game WHERE title = ?", (game,)).fetchone()
    currentTrophies = database.execute("SELECT COUNT(*) FROM trophies WHERE title = ? AND obtained = ?", (game, True,)).fetchone()

    maxTrophiesVal = maxTrophies[0] if maxTrophies else 0  # Default to 0 if no result
    currentTrophiesVal = currentTrophies[0] if currentTrophies else 0  # Default to 0 if no result

    print(f"Selected Game: {game} {currentTrophiesVal}/{maxTrophiesVal}")
    label = CTkLabel(root, text=f"Selected Game: {game} {currentTrophiesVal}/{maxTrophiesVal}", font=("Arial", 18))
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
    trophyFrame = CTkFrame(canvas)
    canvas.create_window((0, 0), window=trophyFrame, anchor="nw")

    # Retrieve the trophies for the selected game
    trophies = getTrophiesList(game)

    # Add a label for each trophy
    for trophy in trophies:
        trophyText = f"{trophy[1]} - {'Obtained' if trophy[4] else 'Not Obtained'}"
        
        # Retrieve the image path for the trophy
        trophyId = trophy[0]
        database.execute('SELECT path FROM images WHERE trophyID = ?', (trophyId,))
        image = database.fetchone()

        iconsDir = os.path.join(dir, "icons")

        # Extract the image filename from the tuple and join it to the icons directory
        if image and image[0]:  # If an image path is found in the database
            imageFilename = image[0]  # Get the first element of the tuple (the path)
        else:
            # Set a default image if no image is found
            imageFilename = "default_image.jpg"

        imagePath = os.path.join(iconsDir, imageFilename)

        # Default image if no image is found for the trophy
        if not imagePath:
            imagePath = os.path.join(iconsDir, "default_image.jpg")  # Default image path

        # Load the image using PIL (for CTkImage compatibility)
        try:
            img = Image.open(imagePath)
            img = img.resize((50, 50))  # Resize the image to 50x50
            imgTk = CTkImage(img, size=(50, 50))  # Ensure to resize using CTkImage size parameter
        except Exception as e:
            imgTk = None  # If there's an error loading the image, just don't display it
            print(f"Error loading image for trophy {trophy[1]}: {e}")

        # Create a frame to hold both the trophy image and text
        trophyFrameInner = CTkFrame(trophyFrame)
        trophyFrameInner.pack(pady=5, anchor="w", fill="x", padx=10)  # Ensure it expands horizontally

        # Add the first image (the one you are initially loading)
        if imgTk:
            # Create a label to display the image, leaving the text empty
            imageLabel = CTkLabel(master=trophyFrameInner, image=imgTk, text="")  # No text
            imageLabel.image = imgTk  # Keep a reference to avoid garbage collection
            imageLabel.pack(side="left", padx=10)

        # Add the trophy name and status text next to the image
        trophyLabel = CTkLabel(master=trophyFrameInner, text=trophyText)
        trophyLabel.pack(side="left", padx=10)

        # Check rarity and add the corresponding image after the text
        rarity = checkRarity(trophy)  # Get the rarity image based on the trophy

        rarityImage = os.path.join(iconsDir, rarity)

        # Load the rarity image
        try:
            rarityImg = Image.open(rarityImage)
            rarityImg = rarityImg.resize((30, 30))  # Resize the image if needed
            rarityImgTk = CTkImage(rarityImg, size=(30, 30))  # Create a CTkImage for compatibility
        except Exception as e:
            rarityImgTk = None
            print(f"Error loading rarity image for trophy {trophy[1]}: {e}")

        # Add the rarity image after the text
        if rarityImgTk:
            rarityImageLabel = CTkLabel(master=trophyFrameInner, image=rarityImgTk, text="")  # No text
            rarityImageLabel.image = rarityImgTk  # Keep a reference to avoid garbage collection
            rarityImageLabel.pack(side="left", padx=10)  # You can adjust the padding as needed

    # Update the scroll region to fit all trophies
    trophyFrame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    # Back to Game List Button
    backBtn = CTkButton(master=root, text="Back to Game List", command=lambda: gameList(root))
    backBtn.place(relx=1.0, rely=0.0, anchor="ne")

    # Delete Game Button
    deleteBtn = CTkButton(master=root, text="Delete Game", command=lambda: deleteData(game))
    deleteBtn.pack(anchor="ne", padx=10, pady=10)

def checkRarity(trophy):
    try:
        # Extract the trophy title (trophy[1] is the title)
        trophyTitle = trophy[1]
        
        # Fetch the rarity of the trophy from the database
        rarity_result = database.execute("SELECT rarity FROM trophies WHERE title = ?", (trophyTitle,)).fetchall()

        # If no rarity is found, return the default image
        if not rarity_result:
            return "default_image.jpg"
        
        # Extract the rarity from the result (assuming there's only one row returned)
        rarity = rarity_result[0][0]  # First element of the first tuple

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
        gameBtn = CTkButton(master=button_frame, text=game, command=lambda game=game: changeWindow(root, game))
        gameBtn.pack(pady=5)

    # Update the scroll region to fit all buttons
    button_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    # Back to Main Menu Button
    backBtn = CTkButton(master=root, text="Back to Main Menu", command=lambda: main(root))
    backBtn.place(relx=1.0, rely=0.0, anchor="ne")

def getTrophiesList(game):
    try:
        database.execute('SELECT trophyID, title, description, rarity, obtained FROM trophies WHERE game = ?', (game,))
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
                path TEXT NOT NULL,
                FOREIGN KEY (trophyID) REFERENCES trophies(trophyID),
                FOREIGN KEY (gameID) REFERENCES game(gameID)
            )
        ''')
        print("Table 'images' created successfully.")
    
    except Exception as e:
        print("Error creating tables:", e)
    
    # Commit changes to the database and close the connection
    database.commit()

#Delete data from the database (functionality not implemented yet)
def deleteData(game):
    print(game)

    gameID = database.execute("SELECT gameID FROM game WHERE title = ?", (game,)).fetchone()
    if gameID:
        gameID = int(gameID[0])  # Ensure gameID is an integer

        # Delete related images
        database.execute("DELETE FROM images WHERE gameID = ?", (gameID,))

        # Delete related trophies
        database.execute('DELETE FROM trophies WHERE game = ?', (game,))

        # Delete the game
        database.execute('DELETE FROM game WHERE title = ?', (game,))

        # Commit the changes
        database.commit()

    else:
        print(f"Game '{game}' not found in the database.")

#Open a new window to input a new game and scrape its data
def newGame(root):
    game = StringVar()  # Variable to hold the game title

    # Create a new popup window for adding a game
    addGame = CTkToplevel(root)
    addGame.title("Add New Game")
    addGame.geometry("400x300")

    # Add a text entry field and a button for entering the game title
    entry = CTkEntry(master=addGame, placeholder_text="What is the new game?", textvariable=game).place(relx=.2, rely=.5)
    btn = CTkButton(master=addGame, text="ENTER", command=lambda: s.getWebPage(game)).place(relx=.2, rely=.7)

#Update the status of a trophy when it's earned
def updateTrophy(trophy):

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