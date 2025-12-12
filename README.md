# Basketball-Stats
Meant for live stat tracking for basketball games.

# Executable File Creation
Run the following line in command prompt with the directory to the files:
pyinstaller --onefile --windowed BasketballGUI.py --add-data "Squirtle.png;." --add-data "Wartortle.png;." --add-data "Blastoise.png;."

This will create an executable file that doesn't rely on any of the files imported once created. Upon use of the executable, necessary files will be created to ensure all necessary data is gathered correctly.

# Footnote on Team 1 and Team 2
All strings with "Reeths-Puffer", "R-P", etc are meant to be "Team 1" and everything with "Team 2" are their opponents.
