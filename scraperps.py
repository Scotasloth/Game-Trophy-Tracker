import requests
import sys
import hashlib
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import connect as conn
import re

db = 'gamedata.accdb'  # Database file name
dir = sys.path[0]  # Get the current working directory
database = conn.connect()
chromeOptions = Options()
# chromeOptions.add_argument("--headless")  # Uncomment to run Chrome in headless mode (background)

# Add game data to the database
def addGameData(game, trophyNum):
    print(game, trophyNum)

    game = game.lower()

    # Check if the game already exists in the database
    exists = database.execute('SELECT COUNT(*) FROM game WHERE title = ? AND platform = ?', (game, "ps",))
    exists = database.fetchone()[0]

    if exists == 0:
        print(f"Game '{game}' does not exist in the database. Inserting...")
        sql = '''
            INSERT INTO game (title, platform, numoftrophies, earned, platinum)
            VALUES (?, ?, ?, ?, ?)
        '''
        database.execute(sql, (game, "ps", trophyNum, 0, False))  # Insert game data
        print(f"Game '{game}' added to the database.")
    else:
        print(f"Game '{game}' already exists in the database.")

    database.commit()

# Add trophy data to the database
def addTrophyData(game, name, description, rarity):
    print(game, name, description, rarity)

    print("I EXISTS BITCHES")
    game = game.lower()

    try:
        print(f"Checking trophy existence: Title: '{name}', Game: '{game}'")

        # Check if the trophy already exists for the game
        existsTrophy = database.execute('SELECT COUNT(*) FROM trophies WHERE title = ? AND game = ? AND platform = ?', (name, game, "ps",))
        existsTrophy = database.fetchone()[0]

        if existsTrophy == 0:
            # Get the gameID for the game
            gameID = database.execute('SELECT gameID FROM game WHERE title = ? AND platform = ?', (game, "ps",)).fetchone()
            
            if gameID:
                gameID = gameID[0]  # Extract gameID
                print(f"GameID for '{game}': {gameID}")

                sql = '''
                    INSERT INTO trophies (gameID, game, title, description, rarity, platform, obtained)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                '''
                database.execute(sql, (gameID, game, name, description, rarity, "ps", False))  # Insert trophy data
                print(f"Inserted trophy: {name} into database.")

                database.commit()

            else:
                print(f"GameID for '{game}' not found in the database.")
        else:
            print(f"Trophy '{name}' for game '{game}' already exists in the database.")

    except Exception as e:
        print(f"Error while checking or adding trophy: {e}")

# Add image data for a trophy to the database
def addImage(game, trophy, imagePath):

    # Get the gameID and trophyID
    gameID = database.execute("SELECT gameID FROM game WHERE title = ?", (game,)).fetchone()[0]
    trophyID = database.execute("SELECT trophyID FROM trophies WHERE title = ?", (trophy,)).fetchone()[0]

    try:
        sql = '''
            INSERT INTO images (trophyID, gameID, platform, path)
            VALUES (?, ?, ?, ?)
        '''
        # Insert the image path as a file attachment
        database.execute(sql, (trophyID, gameID, "PS", imagePath))
        database.commit()
        print(f"Image for trophy '{trophy}' added to database.")

    except Exception as e:
        print(f"Error in addImage: {e}")

# Scroll the page to load more content
def scrollPage(driver, scrollDistance=1000, waitTime=5):
    """Scroll down the page by a specified distance and wait for lazy-loaded content to appear."""
    print(f"Executing scroll: Scrolling by {scrollDistance} pixels.")
    try:
        # Scroll the page down by the specified distance
        driver.execute_script(f"window.scrollBy(0, {scrollDistance});")
        time.sleep(waitTime)  # Wait for content to load
        print(f"Scrolled down by {scrollDistance}. Waiting for {waitTime} seconds.")
        
    except Exception as e:
        print(f"Error while scrolling: {e}")

# Function to scrape the web page and process the trophy data
def getWebPage(game):
    gameUrl = game.get().replace(" ", "-").lower()
    gameName = game.get()
    print(f"Game Name: {gameUrl}")

    url = f"https://www.playstationtrophies.org/game/{gameUrl}/trophies/"

    # Set up the Selenium WebDriver
    chromeOptions = Options()
    driver = webdriver.Chrome(options=chromeOptions)

    try:
        # Open the webpage
        driver.get(url)
        time.sleep(3)  # Wait for the page to load initially

        try:
            button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div[2]/div[2]/div[2]/div[2]/button[1]")))
            button.click()
            print("Button clicked")
            time.sleep(3)
        except Exception as e:
            print("Error clicking button:", e)

        try:
            h3Elements = driver.find_elements(By.CLASS_NAME, 'h-3')
            
            if len(h3Elements) > 1:
                trophynumText = h3Elements[1].text
                print("Trophy Count Text:", trophynumText)

                trophyCountMatch = re.search(r"(\d+)\s+trophies", trophynumText)
                if trophyCountMatch:
                    trophyCount = int(trophyCountMatch.group(1))
                    print(f"Trophy Count: {trophyCount}")

                    addGameData(gameName, trophyCount)
                else:
                    print("Trophy count not found in the text:", trophynumText)
            else:
                print("Not enough <h3> tags found.")
        
        except Exception as e:
            print("Error while scraping trophy data:", e)

        imagesScraped = 0
        maxScrollAttempts = 10
        scrollAttempts = 0
        totalTrophies = 0

        while scrollAttempts < maxScrollAttempts:
            allTrophyElements = driver.find_elements(By.XPATH, "//ul[contains(@class, 'achilist')]/li[contains(@class, 'achilist__item')]")
            print(f"Found {len(allTrophyElements)} trophies after scroll {scrollAttempts}.")

            for trophyElement in allTrophyElements[totalTrophies:]:
                title = "No title found"
                description = "No description found"
                rarity = "Unknown"
                trophyImages = []

                try:
                    titleElement = trophyElement.find_element(By.XPATH, ".//div[contains(@class, 'achilist__header')]//h4[contains(@class, 'achilist__title')]")
                    title = titleElement.text
                    print(f"Trophy: {title}")
                except Exception as e:
                    print("Error while scraping trophy title:", e)

                description = "No description found"
                try:
                    descriptionElement = trophyElement.find_element(By.XPATH, ".//div[@class='achilist__data']//p[not(ancestor::div[@class='achilist__header'])]") 
                    description = descriptionElement.text
                    print(f"Description: {description}")
                except Exception as e:
                    print("Error while scraping description:", e)

                rarity = "Unknown"
                try:
                    rarityImage = trophyElement.find_element(By.XPATH, ".//div[@class='achilist__value']//img")
                    raritySrc = rarityImage.get_attribute("src")
                    rarity = getRarity(raritySrc)
                    print(f"Rarity: {rarity}")
                except Exception as e:
                    print("Error while scraping rarity:", e)

                try:
                    addTrophyData(gameName, title, description, rarity)
                except Exception as e:
                    print(f"Error while adding trophy data: {e}")

                try:
                    imageElement = trophyElement.find_element(By.XPATH, ".//div[@class='list__pic']//img")
                    imageUrl = imageElement.get_attribute("src")
                    if imageUrl:
                        trophyImages.append(imageUrl)
                    print("Trophy Images:", trophyImages)

                    iconsDir = os.path.join(os.getcwd(), "icons")

                    if not os.path.exists(iconsDir):
                        os.makedirs(iconsDir)

                    for idx, trophyImage in enumerate(trophyImages, start=1):

                        titleFix = re.sub(r'[^a-zA-Z0-9_]', '', title)
                        path = os.path.join(iconsDir, f"{gameName}_{titleFix}_{idx}_ps.jpg")
                        downloadImages(trophyImage, path)

                        img = (f"{gameName}_{titleFix}_{idx}_ps.jpg")
                        addImage(gameName, title, img)

                except Exception as e:
                    print("Error with image for trophy:", e)

                imagesScraped += 1

                if imagesScraped % 5 == 0:
                    print("Scrolling after 5 images...")
                    scrollPage(driver)
                    scrollAttempts += 1

            newTrophyElements = driver.find_elements(By.XPATH, "//ul[contains(@class, 'achilist')]/li[contains(@class, 'achilist__item')]")
            print(f"New trophies found after scroll {scrollAttempts}: {len(newTrophyElements)}")

            if len(newTrophyElements) == len(allTrophyElements):
                print("No new trophies visible after scroll, stopping scraping.")
                break

            totalTrophies = len(newTrophyElements)

    except Exception as e:
        print("Error while scraping webpage:", e)

    finally:
        driver.quit()

# Get rarity based on image source
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

# Convert image to binary
def convertBinary(imgPath):
    with open(imgPath, 'rb') as f:
        return f.read()

# Download image from URL
def downloadImages(imageUrl, path):
    try:
        response = requests.get(imageUrl)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            print(f"Image saved at {path}")
        else:
            print(f"Failed to download image {imageUrl}. HTTP Status: {response.status_code}")
    except Exception as e:
        print(f"Error downloading image {imageUrl}: {e}")