#Scrape the webpage to get the game data and trophy information.
import requests
import sys
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import connect as conn

db = 'gamedata.accdb'  # Database file name
dir = sys.path[0]
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Uncomment to run Chrome in headless mode (background)

def addGameData(game, trophynum):
    print(game, trophynum)

    game = game.lower()
    database = conn.connect()

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
    database = conn.connect()

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
    database = conn.connect()

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

def getWebPage(game):
    
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