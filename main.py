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
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from PIL import Image as PilImage
from functools import partial
import pyodbc
import connect as conn
import scraperps as ps
import scraperxbox as xb
import scraperpc as pc
from PIL import ImageEnhance
import pygame


# Global variables for database and chrome options
#db = 'gamedata.accdb'  # Database file name
dir = sys.path[0]  # Current directory of the program
database = conn.connect()

pygame.mixer.init()
trophyObtainedEffect = pygame.mixer.Sound(f'{dir}/sounds/trophyObtained.mp3')


class TrophyTrackerApp(App):

    # Main window that starts the program
    def main(self, root):
        # Create the main layout as a BoxLayout with vertical orientation
        self.mainLayout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.mainLayout.size_hint = (1, 1)  # Ensure main layout fills the entire window

        # Menu Layout (Ensure it fills the width and has fixed height)
        menuLayout = BoxLayout(size_hint_y=None, height=200)
        menuLayout.size_hint_x = 1  # Make the menu layout fill the width
        menuLayout.add_widget(Button(text="Initialize", size_hint_x=0.33, on_press=lambda instance: self.create()))
        menuLayout.add_widget(Button(text="Add new game", size_hint_x=0.33, on_press=lambda instance: self.newGame(root)))
        menuLayout.add_widget(Button(text="View Games", size_hint_x=0.33, on_press=lambda instance: self.gameList(root)))
        self.mainLayout.add_widget(menuLayout)

        # Recent Games Layout (GridLayout that fills the width, dynamic height)
        recentLayout = GridLayout(cols=1, size_hint_y=None, padding=[10, 0, 10, 0], spacing=5)
        recentLayout.bind(minimum_height=recentLayout.setter('height'))  # Adjust height based on content
        recentLayout.size_hint_x = 1  # Ensure it fills the entire width

        # Add a header label for "RECENT"
        recentLayout.add_widget(Label(text="RECENT:", font_size=25, size_hint_y=None, height=40))

        # Simulate the recent game data
        recentGame1 = self.updateRecent(1)
        recentGame2 = self.updateRecent(2)
        recentGame3 = self.updateRecent(3)
        recentGame4 = self.updateRecent(4)
        recentGame5 = self.updateRecent(5)

        # Add recent games dynamically to the layout
        for i, recentGame in enumerate([recentGame1, recentGame2, recentGame3, recentGame4, recentGame5], start=1):
            try:
                gameInfo = f"{recentGame[4].upper()} - {recentGame[3]}"
                recentLayout.add_widget(Label(text=gameInfo, size_hint_x=1, size_hint_y=None, height=40))  # Fixed height for each label
            except Exception as e:
                print(f"Error no data in recent game {i}: {e}")

        # Add the recent games in a scrollable view (takes up full width and available height)
        scrollView = ScrollView(size_hint=(1, None), height=400)  # Adjust scrollView height if needed
        scrollView.add_widget(recentLayout)
        self.mainLayout.add_widget(scrollView)

        # Add the main layout to the root (Ensure root widget takes the full screen)
        root.add_widget(self.mainLayout)

        # Ensure the root widget takes up the full space and is centered
        root.size_hint = (1, 1)
        root.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

    def print_widget_size(self, widget):
        print(f"Widget {widget} size: {widget.size}")

    def updateRecent(self, val):
        recent = 0
        try:
            recent = database.execute("SELECT * FROM recent WHERE recentID = ?", (val,)).fetchone()
        except Exception as e:
            print(f"Error with getting recent {e}")
        return recent

    def playSound(self):
        trophyObtainedEffect.play()

    def choosePlatform(self, game, platform):
        print(f"{game} {platform}")
        if platform == "ps" or platform == "playstation" or platform == "ps5":
            ps.getWebPage(game)

        elif platform == "xbox":
            xb.getWebPage(game)

    def newGame(self, root):
        # Clear the current layout to remove previous widgets
        root.clear_widgets()

        # Create a new layout for the new game form
        newGamePopup = BoxLayout(orientation='vertical', padding=20)
        newGamePopup.add_widget(Label(text="Enter new game details"))

        # Add TextInputs for the game name and platform
        self.game = TextInput(hint_text="Enter Game Name")
        self.platform = TextInput(hint_text="Enter The Platform")
        newGamePopup.add_widget(self.game)
        newGamePopup.add_widget(self.platform)

        # Create a "Create Game" button
        newGameButton = Button(text="Create Game")
        
        # Bind the button press to first call the choosePlatform function
        # Then, clear the current widgets and return to the main menu
        newGameButton.bind(on_press=lambda instance: (
            self.choosePlatform(self.game.text, self.platform.text),  # Call the platform and game creation logic
            root.clear_widgets(),  # Clear current widgets
            self.main(root)  # Return to the main menu
        ))

        newGamePopup.add_widget(newGameButton)

        # Add the new game layout to the root (replaces the current layout)
        root.add_widget(newGamePopup)

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
        root.clear_widgets()

        # Main layout setup
        mainLayout = BoxLayout(orientation='vertical', padding=20, spacing=10, size_hint_y=None)
        mainLayout.bind(minimum_height=mainLayout.setter('height'))
        scrollView = ScrollView(size_hint=(1, None), height=600)
        scrollView.add_widget(mainLayout)
        root.add_widget(scrollView)

        # Get max and current trophy count
        maxTrophies = database.execute("SELECT numoftrophies FROM game WHERE gameID = ? AND platform = ?", (game, platform)).fetchone()
        currentTrophies = database.execute("SELECT earned FROM game WHERE gameID = ? AND platform = ?", (game, platform)).fetchone()

        maxTrophiesVal = maxTrophies[0] if maxTrophies else 0
        currentTrophiesVal = currentTrophies[0] if currentTrophies else 0

        # Top label showing the trophy progress
        trophyLabelTop = Label(text=f"Selected Game: {title} {currentTrophiesVal}/{maxTrophiesVal}", font_size=18, size_hint_y=None, height=50, halign="center")
        mainLayout.add_widget(trophyLabelTop)

        # Grid layout for trophies
        trophyGridLayout = GridLayout(cols=1, padding=10, spacing=10, size_hint_y=None)
        trophyGridLayout.bind(minimum_height=trophyGridLayout.setter('height'))
        mainLayout.add_widget(trophyGridLayout)

        trophies = self.getTrophiesList(game)

        for trophy in trophies:
            trophyText = f"{trophy[1]} - {'Obtained' if trophy[4] else 'Not Obtained'}"
            trophyId = trophy[0]
            
            # Get image path and rarity for the trophy
            image = database.execute('SELECT path FROM images WHERE trophyID = ?', (trophyId,)).fetchone()
            rarity = database.execute("SELECT rarity FROM trophies WHERE trophyID = ?", (trophyId,)).fetchone()[0]
            iconsDir = os.path.join(dir, "icons")
            imageFilename = image[0] if image else "default_image.jpg"
            imagePath = os.path.join(iconsDir, imageFilename)
            rarityImgPath = self.checkRarity(rarity)
            imgRPath = os.path.join(iconsDir, rarityImgPath)

            # Create a frame for the trophy image and its info
            trophyFrameInner = BoxLayout(orientation="vertical", size_hint_y=None, height=150, padding=10, spacing=10, pos_hint={'center_x': 0.5})
            trophyGridLayout.add_widget(trophyFrameInner)

            # Load and display the trophy image
            if os.path.exists(imagePath):
                img = KivyImage(source=imagePath, size_hint=(None, None), size=(50, 50))
                img.bind(on_touch_down=partial(self.onImageClick, trophy=trophy, trophyLabelTop=trophyLabelTop))  # Bind click event to this specific image
                trophyFrameInner.add_widget(img)

                # If trophy is not obtained, make image grayscale
                if not trophy[4]:
                    img.color = [0.5, 0.5, 0.5, 1]  # Apply grayscale

            # Create a horizontal layout for the rarity image
            rarityLayout = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, padding=10, spacing=10, pos_hint={'center_x': 0.5})
            trophyFrameInner.add_widget(rarityLayout)

            if os.path.exists(imgRPath):
                rarityImg = KivyImage(source=imgRPath, size_hint=(None, None), size=(30, 30))
                rarityLayout.add_widget(rarityImg)

            # Display the trophy name and description
            trophyLabel = Label(text=trophy[1], size_hint_y=None, height=30, halign="center", font_size=16)
            trophyFrameInner.add_widget(trophyLabel)

            descLabel = Label(text=trophy[2], size_hint_y=None, height=30, halign="center", font_size=14)
            trophyFrameInner.add_widget(descLabel)

        # Buttons for going back and deleting the game
        buttonsLayout = BoxLayout(size_hint_y=None, height=80, spacing=10)
        mainLayout.add_widget(buttonsLayout)

        backBtn = Button(text="Back to Game List", size_hint=(None, None), size=(200, 50))
        backBtn.bind(on_press=lambda instance: (root.clear_widgets(), self.gameList(root)))
        buttonsLayout.add_widget(backBtn)

        deleteBtn = Button(text="Delete Game", size_hint=(None, None), size=(200, 50))
        deleteBtn.bind(on_press=lambda instance: self.deleteData(game))
        buttonsLayout.add_widget(deleteBtn)

    # Function to handle image click and mark trophy as obtained
    def onImageClick(self, instance, touch, trophy, trophyLabelTop):
        # Ensure we're dealing with a valid touch on the image
        if instance.collide_point(touch.x, touch.y):
            self.playSound()

            try:
                trophyStatus = database.execute("SELECT obtained FROM trophies WHERE trophyID = ?", (trophy[0],)).fetchone()

                if trophyStatus and trophyStatus[0]:  # If obtained is True
                    print(f"Trophy {trophy[1]} is already obtained. No changes made.")
                    return  # Return early if trophy is already obtained
            
                # Step 1: Update the trophy status in the database
                database.execute("UPDATE trophies SET obtained = ? WHERE trophyID = ?", (True, trophy[0]))  # Set 'obtained' to True
                database.commit()

                # Step 2: Update the trophy image to full color
                imagePath = self.getImagePathForTrophy(trophy)
                
                # Use PIL to open the image and resize it for Kivy
                img_pil = PilImage.open(imagePath)
                img_pil = img_pil.resize((50, 50))  # Resize to match Kivy widget size

                # Make the image grayscale if the trophy is not obtained
                if not trophy[4]:
                    enhancer = ImageEnhance.Color(img_pil)
                    img_pil = enhancer.enhance(0.0)  # Grayscale
                else:
                    enhancer = ImageEnhance.Color(img_pil)
                    img_pil = enhancer.enhance(1.0)  # Full color

                # Convert PIL image to a Kivy texture
                texture = Texture.create(size=(50, 50))
                texture.blit_buffer(img_pil.tobytes(), colorfmt='rgb', bufferfmt='ubyte')

                # Step 3: Update the image in the Kivy widget
                instance.texture = texture  # Update the image widget's texture

                # Step 4: Update the earned trophy count for the game
                self.updateTrophy(trophy, trophyLabelTop)

            except Exception as e:
                print(f"Error updating trophy status: {e}")

            # Add the trophy to the recent list
            self.addRecent(trophy)

# Function to get the image path for the trophy
    def getImagePathForTrophy(self, trophy):
        trophyId = trophy[0]
        database.execute('SELECT path FROM images WHERE trophyID = ?', (trophyId,))
        image = database.fetchone()
        iconsDir = os.path.join(dir, "icons")
        return os.path.join(iconsDir, image[0]) if image else os.path.join(iconsDir, "default_image.jpg")

    def checkRarity(self, rarity):
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
        # Clear the current layout to remove previous widgets
        root.clear_widgets()

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
        # Bind the back button to clear the layout and go back to the main menu
        backBtn.bind(on_press=lambda btn: (root.clear_widgets(), self.main(root)))  # Clear and return to main menu
        root.add_widget(backBtn)
    
    #Update the status of a trophy when it's earned
    def updateTrophy(self, trophy, trophyLabel):
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
                        """, (True, gameID))

            database.commit()

            # Step 3: Update the label to reflect the new earned count
            currentTrophies = database.execute("SELECT earned FROM game WHERE gameID = ?", (gameID,)).fetchone()[0]
            maxTrophies = database.execute("SELECT numoftrophies FROM game WHERE gameID = ?", (gameID,)).fetchone()[0]

            # Dynamically update the trophy label here
            trophyLabel.text = f"Selected Game: {game} {currentTrophies}/{maxTrophies}"

        except Exception as e:
            print(f"Error updating game progress: {e}")

    def getTrophiesList(self, game):
        try:
            database.execute('SELECT trophyID, title, description, rarity, obtained FROM trophies WHERE gameID = ?', (game,))
            trophies = database.fetchall()
            return trophies

        except Exception as e:
            print("Error", e)
            return []

    # Create the required database tables if they don't exist
    def create(self):
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
    def deleteData(self, game):
        print(game)

        gameID = database.execute("SELECT gameID FROM game WHERE gameID = ?", (game,)).fetchone()
        if gameID:
            gameID = int(gameID[0])  # Ensure gameID is an integer

            # Delete entries from images, trophies, and game tables
            database.execute("DELETE FROM recent WHERE gameID = ?", (gameID,))
            database.execute("DELETE FROM images WHERE gameID = ?", (gameID,))
            database.execute("DELETE FROM trophies WHERE gameID = ?", (gameID,))
            database.execute("DELETE FROM game WHERE gameID = ?", (gameID,))
            database.commit()
        else:
            print(f"Game with ID {game} not found in the database.")

class MyApp(App):
    def build(self):
        # Set the window size
        Window.size = (800, 600)  # You can adjust this size if necessary

        # Create and return a BoxLayout as the root
        root = BoxLayout()
        
        # Initialize the TrophyTrackerApp
        gameApp = TrophyTrackerApp()
        
        # Call the main method of TrophyTrackerApp to build the UI
        gameApp.main(root)
        
        return root

if __name__ == "__main__":
    MyApp().run()