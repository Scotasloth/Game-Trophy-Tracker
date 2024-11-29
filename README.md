# Game-Trophy-Tracker (Python Project)
A Python program that aims to act as a tracker for game trophies and achievements. Works for both Playstation and Xbox.
## **Features**

- **Tracks the trophy progress for games the user specifies.**
- **Gets information about game and its trohpies**
- **Makes use of web-scraping to retrieve information**
- **Stores data in an SQLite3 database**
  
## **Prerequisites**

Before running this project, make sure you have the following installed:

- **Python 3.x**: You can download it from [python.org](https://www.python.org/downloads/).

## **Required Python Libraries**

You will need to install the following libraries:

SQLite3: For connecting and interacting with the SQLite database.

Kivy: For creating a modern and customizable graphical user interface (GUI).

selenium: For automating the web browser to scrape trophy data.

## **Usage**

Adding New Game:
You can add a new game by clicking the "Add New Game" button in the main GUI window. The program will prompt you to enter the name of the game.
After entering the game name, the program will fetch information about the game's trophies (via web scraping) and display the details in the application.

Database Actions:
The program will automatically create and maintain the following tables in the Access database:

game: Stores basic game information like game title, number of trophies, platform, and platinum status.

trophies: Stores trophy details for each game, such as trophy title, description, rarity, platform, and whether it has been obtained.

images: Stores all information needed to display images for trophies.

recent: Is used to store the 5 most recent trophies earned to display them on the main menu

If you want to reset or delete a games data, you can press the "Delete Data" button in the program's interface to clear the game from the database.

Handling Errors:
The program may encounter errors while scraping web pages (e.g., if the game title doesn’t match the expected format). These will be displayed in the output console. If you encounter any issues, make sure that the game title is correctly formatted (lowercase, no spaces). 

If an image failed to be retrieved from the webpage or download correctly a default image will take its place to allow the trophy to still be marked as obtained.

## **Installation**

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/Scotasloth/Game-Trophy-Tracker.git

2. If database is already populated run the delete data button to reset the program
