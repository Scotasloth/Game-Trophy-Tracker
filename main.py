import sys
import kivy
import os
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image as KivyImage
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.graphics.texture import Texture
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from PIL import Image as PilImage
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


class TrophyTrackerApp(App):
    def build(self):
        # Initialize the root layout (BoxLayout)
        root = BoxLayout(orientation='vertical')

        # Set the appearance for Kivy (if necessary)
        Window.clearcolor = (0.1, 0.1, 0.1, 1)  # Dark mode-like background
        
        # Call the main menu to set up the initial view
        self.main(root)  # This will call the main method
        
        return root

    # Main window that starts the program
    def main(self, root):
        # Create buttons for the main menu
        menuLayout = BoxLayout(size_hint_y=None, height=200)
        menuLayout.add_widget(Button(text="Initialize", on_press=lambda instance: self.create()))  # Removed self as argument
        menuLayout.add_widget(Button(text="Add new game", on_press=lambda instance: self.newGame()))  # Removed self as argument
        menuLayout.add_widget(Button(text="View Games", on_press=lambda instance: self.gameList()))  # Removed self as argument
        root.add_widget(menuLayout)

        # Display recent games
        recentLayout = GridLayout(cols=1, size_hint_y=None)
        recentLayout.bind(minimum_height=recentLayout.setter('height'))

        recentGame1 = self.updateRecent(1)
        recentGame2 = self.updateRecent(2)
        recentGame3 = self.updateRecent(3)
        recentGame4 = self.updateRecent(4)
        recentGame5 = self.updateRecent(5)

        recentLayout.add_widget(Label(text="RECENT:", font_size=25))

        for i, recentGame in enumerate([recentGame1, recentGame2, recentGame3, recentGame4, recentGame5], start=1):
            try:
                gameInfo = f"{recentGame[4].upper()} - {recentGame[3]}"
                recentLayout.add_widget(Label(text=gameInfo))
            except Exception as e:
                print(f"Error no data in recent game {i}: {e}")

        # Add the recent games in a scrollable view
        scrollView = ScrollView()
        scrollView.add_widget(recentLayout)
        root.add_widget(scrollView)

    def updateRecent(self, val):
        recent = 0
        try:
            recent = database.execute("SELECT * FROM recent WHERE recentID = ?", (val,)).fetchone()
        except Exception as e:
            print(f"Error with getting recent {e}")
        return recent

    def playSound(self):
        trophyObtainedEffect.play()

    def addRecent(self, trophy):
        gameID = database.execute("SELECT gameID FROM trophies WHERE trophyID = ?", (trophy[0],)).fetchone()
        platform = database.execute("SELECT platform FROM trophies WHERE trophyID = ?", (trophy[0],)).fetchone()
        game = database.execute("SELECT game FROM trophies WHERE trophyID = ?", (trophy[0],)).fetchone()

        try:
            # Step 1: Check if the table is empty. If it is, no need to update the recentID.
            count =  database.execute("SELECT COUNT(*) FROM recent").fetchone()[0]
            
            if count > 0:
                # If there are existing rows, increment the recentID for all existing rows
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
                    """, (newRecentID, row[0]))

            # Step 2: Insert the new row with recentID = 1 (it will be the first row)
            database.execute("""
                INSERT INTO recent (recentID, gameID, trophyID, trophy, game, platform)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (1, gameID[0], trophy[0], trophy[1], game[0], platform[0]))
            
            # Step 3: Ensure the table never has more than 5 rows
            if count >= 5:
                # If there are 5 or more rows, delete the row with the highest recentID (most recent)
                database.execute("""
                    DELETE FROM recent
                    WHERE recentID > 5
                """)

            # Commit the transaction
            database.commit()

        except Exception as e:
            print(f"Unexpected error: {e}")

    def getTitle(self):
        try:
            database.execute('SELECT gameID FROM game ORDER BY title ASC')
            games = database.fetchall()
            return [game[0] for game in games]
        except Exception as e:
            print("Error retrieving titles:", e)
            return []

    # Function to clear and change the content of the window to display the selected game
    def changeWindow(self, root, game, title, platform):
        # Clear the window before adding new content
        for widget in root.children:
            root.remove_widget(widget)

        # Retrieve the max number of trophies for the selected game
        maxTrophies = database.execute("SELECT numoftrophies FROM game WHERE gameID = ? AND platform = ?", (game, platform)).fetchone()
        currentTrophies = database.execute("SELECT earned FROM game WHERE gameID = ? AND platform = ?", (game, platform)).fetchone()

        maxTrophiesVal = maxTrophies[0] if maxTrophies else 0
        currentTrophiesVal = currentTrophies[0] if currentTrophies else 0

        # Label for showing current trophies earned
        trophyLabelTop = Label(text=f"Selected Game: {title} {currentTrophiesVal}/{maxTrophiesVal}", font_size=18)
        root.add_widget(trophyLabelTop)

        # Display the trophies for this game with a scrollbar
        frame = BoxLayout(orientation="vertical", padding=10, spacing=10)
        root.add_widget(frame)

        scrollView = ScrollView()
        frame.add_widget(scrollView)

        trophyGridLayout = GridLayout(cols=1, padding=10, spacing=10, size_hint_y=None)
        trophyGridLayout.bind(minimum_height=trophyGridLayout.setter('height'))
        scrollView.add_widget(trophyGridLayout)

        trophies = self.getTrophiesList(game)

        for index, trophy in enumerate(trophies):
            print("THIS IS IN changeWindow,", index)
            trophyText = f"{trophy[1]} - {'Obtained' if trophy[4] else 'Not Obtained'}"
            
            trophyId = trophy[0]
            database.execute('SELECT path FROM images WHERE trophyID = ?', (trophyId,))
            image = database.fetchone()
            rarity = database.execute("SELECT rarity FROM trophies WHERE trophyID = ?", (trophyId,)).fetchone()[0]
            
            iconsDir = os.path.join(dir, "icons")
            imageFilename = image[0] if image else "default_image.jpg"
            imagePath = os.path.join(iconsDir, imageFilename)
            rarityImgPath = self.checkRarity(rarity)
            imgRPath = os.path.join(iconsDir, rarityImgPath)

            try:
                img = KivyImage.open(imagePath)
                if not trophy[4]:  # If the trophy is not obtained
                    enhancer = ImageEnhance.Color(img)
                    img = enhancer.enhance(0.0)  # Make the image grayscale

                img = img.resize((50, 50))
                imgTk = Texture.create(size=(50, 50))
                imgTk.blit_buffer(img.tobytes(), colorfmt='rgb', bufferfmt='ubyte')

            except Exception as e:
                imgTk = None
                print(f"Error loading image for trophy {trophy[1]}: {e}")

            # Create a frame to hold the image and the text
            trophyFrameInner = BoxLayout(orientation="horizontal", size_hint_y=None, height=50)
            trophyGridLayout.add_widget(trophyFrameInner)

            # Display the trophy image
            if imgTk:
                imageLabel = KivyImage(texture=imgTk)
                trophyFrameInner.add_widget(imageLabel)

                if not trophy[4]:  # Trophy not obtained, make image clickable
                    imageLabel.bind(on_touch_down=lambda instance, event, t=trophy, label=imageLabel, trophyLabelTop=trophyLabelTop: self.onImageClick(t, label, trophyLabelTop))

            # Process the rarity image
            try:
                imgR = KivyImage.open(imgRPath)
                imgR = imgR.resize((50, 50))
                imgRTk = Texture.create(size=(50, 50))
                imgRTk.blit_buffer(imgR.tobytes(), colorfmt='rgb', bufferfmt='ubyte')

            except Exception as e:
                imgRTk = None
                print(f"Error displaying trophy rarity: {e}")

            # Display the rarity image if it's successfully loaded
            if imgRTk:
                rarityLabel = KivyImage(texture=imgRTk)
                trophyFrameInner.add_widget(rarityLabel)

            # Display the trophy description
            trophyLabel = Label(text=trophyText)
            trophyFrameInner.add_widget(trophyLabel)

            # Create the description label (this is the description or additional information)
            descLabel = Label(text=trophy[2])
            trophyFrameInner.add_widget(descLabel)

        # Back button and delete button
        backBtn = Button(text="Back to Game List", on_press=lambda instance: self.gameList(root))
        backBtn.size_hint = (None, None)
        backBtn.size = (200, 50)
        backBtn.pos_hint = {"right": 1, "top": 1}
        root.add_widget(backBtn)

        deleteBtn = Button(text="Delete Game", on_press=lambda instance: self.deleteData(game))
        deleteBtn.size_hint = (None, None)
        deleteBtn.size = (200, 50)
        deleteBtn.pos_hint = {"right": 1, "top": 0.9}
        root.add_widget(deleteBtn)

    # Function to handle image click and mark trophy as obtained
    def onImageClick(self, trophy, label, trophyLabelTop):
        self.playSound()

        try:
            # Step 1: Update the trophy status in the database
            database.execute("UPDATE trophies SET obtained = ? WHERE trophyID = ?", (True, trophy[0]))  # Set 'obtained' to True
            database.commit()

            # Step 2: Update the trophy image to full color
            imagePath = self.getImagePathForTrophy(trophy)
            img = PilImage.open(imagePath)
            
            # If the trophy is not obtained, make it grayscale
            if not trophy[4]:
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.0)  # Make the image grayscale

            img = img.resize((50, 50))

            # Convert the PIL image to a Kivy texture
            texture = Texture.create(size=(50, 50))
            texture.blit_buffer(img.tobytes(), colorfmt='rgb', bufferfmt='ubyte')

            # Update the image in the Kivy widget
            label.texture = texture

            # Step 3: Update the earned trophy count for the game
            self.updateTrophy(trophy, trophyLabelTop)

        except Exception as e:
            print(f"Error updating trophy status: {e}")

        # Add the trophy to the recent list
        self.addRecent(trophy)

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
    def gameList(self, root):
        # Clear the window before adding new content
        for widget in root.children[:]:
            widget.clear_widgets()

        # Create a scrollable layout for the game buttons and info
        scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        scroll_layout = GridLayout(cols=1, padding=10, spacing=10, size_hint_y=None)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_view.add_widget(scroll_layout)
        
        # Retrieve the game titles from the database
        titles = self.getTitle()

        # Add a button for each game title
        for game in titles:
            plat = database.execute("SELECT platinum FROM game WHERE gameID = ?", (game,)).fetchone()[0]
            platform = database.execute("SELECT platform FROM game WHERE gameID = ?", (game,)).fetchone()
            gameName = database.execute("SELECT title FROM game WHERE gameID = ?", (game,)).fetchone()

            platform = platform[0] if platform else "Unknown"  # Default to "Unknown" if no platform is found
            gameName = gameName[0] if gameName else "Unknown Game"  # Default to "Unknown Game" if no game name is found

            # Create game button with color based on platform
            if plat == True:
                gameBtn = Button(text=f"{gameName.upper()} - {platform.upper()}", background_color=(1, 0.843, 0, 1), color=(0, 0, 0, 1), size_hint_y=None, height=40)
                gameBtn.bind(on_press=lambda btn, game=game, gameName=gameName, platform=platform: self.changeWindow(root, game, gameName, platform))
            elif platform == "xbox":
                gameBtn = Button(text=f"{gameName.upper()} - {platform.upper()}", background_color=(0, 0.5, 0, 1), color=(1, 1, 1, 1), size_hint_y=None, height=40)
                gameBtn.bind(on_press=lambda btn, game=game, gameName=gameName, platform=platform: self.changeWindow(root, game, gameName, platform))
            else:
                gameBtn = Button(text=f"{gameName.upper()} - {platform.upper()}", background_color=(0.5, 0.5, 0.5, 1), color=(1, 1, 1, 1), size_hint_y=None, height=40)
                gameBtn.bind(on_press=lambda btn, game=game, gameName=gameName, platform=platform: self.changeWindow(root, game, gameName, platform))

            # Add the game button to the scroll layout
            scroll_layout.add_widget(gameBtn)

            # Retrieve the earned and total trophies for the game
            earned = database.execute("SELECT earned FROM game WHERE gameID = ?", (game,)).fetchone()[0]
            total = database.execute("SELECT numoftrophies FROM game WHERE gameID = ?", (game,)).fetchone()[0]

            # Create a label for the earned/totals trophies
            gameLbl = Label(text=f"{earned}/{total}", size_hint_y=None, height=30)
            scroll_layout.add_widget(gameLbl)

        # Add the scroll view to the root layout
        root.add_widget(scroll_view)

        # Create a Back button to return to the main menu
        backBtn = Button(text="Back to Main Menu", size_hint=(None, None), size=(200, 50), pos_hint={'right': 1, 'top': 1})
        backBtn.bind(on_press=lambda btn: self.main(root))
        root.add_widget(backBtn)

    def getTrophiesList(game):
        try:
            database.execute('SELECT trophyID, title, description, rarity, obtained FROM trophies WHERE gameID = ?', (game,))
            trophies = database.fetchall()
            return trophies

        except Exception as e:
            print("Error", e)
            return []

    # Create the required database tables if they don't exist
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

    # Delete data from the database (functionality not implemented yet)
    def deleteData(game):
        print(game)

        gameID = database.execute("SELECT gameID FROM game WHERE gameID = ?", (game,)).fetchone()
        if gameID:
            gameID = int(gameID[0])  # Ensure gameID is an integer

            # Delete entries from images, trophies, and game tables
            database.execute("DELETE FROM images WHERE gameID = ?", (gameID,))
            database.execute("DELETE FROM trophies WHERE gameID = ?", (gameID,))
            database.execute("DELETE FROM game WHERE gameID = ?", (gameID,))
            database.commit()
        else:
            print(f"Game with ID {game} not found in the database.")