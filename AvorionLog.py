# pip install termcolor

import os
import re
import sys
import json
import time
import glob
import collections
import winsound
from datetime import datetime
from termcolor import colored

#from colorama import Fore, init

# Path to the latest log file. New gets created every time you log in to gameserver.
appdatapath = os.path.join(os.getenv('APPDATA'), 'Avorion')

# Get a list of all files that match "clientlog" in the directory
files = glob.glob(os.path.join(appdatapath, '*clientlog*'))
# Sort the files by modification time in descending order
files.sort(key=os.path.getmtime, reverse=True)
# Get the first file in the sorted list
path = files[0] if files else None
# debug
print(path)

# Load the settings from the settings.json file
if os.path.exists('settings.json'):
    with open('settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
else:
    print("settings.json file does not exist")

# Get the color patterns from the settings
color_patterns = settings['colors']
# Load the word filter from the settings
word_filter = settings['wordfilter']
# Load the pattern colors from the settings, or an empty dictionary if the key does not exist
pattern_colors = settings['patternColors']
# This line of code is retrieving the value of 'notify' from the 'settings' dictionary.
notify = settings['notify']
# This line of code is initializing the variable 'last_played' with the value 0.
last_played = 0
delay = 5  # Delay in seconds

# This function, 'colorize', takes in a string 'line' and applies various color patterns to it.
# It first applies global color patterns to the entire line, then applies specific color patterns to parts of the line.
# If the line contains any word from the 'notify' list, it plays a sound, provided that a certain delay has passed since the last sound was played.
# If the line contains any word from the 'word_filter' list, the function returns None.
# Otherwise, it returns the colorized line.
def colorize(line, default_color=None):
    global last_played  # Use the global last_played variable

    # If a default color is provided, color the entire line with it
    if default_color is not None:
        line = colored(line, default_color)

    # First, color the entire line based on color_patterns
    for color, patterns in color_patterns.items():
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                line = colored(line, color)

    # Then, color the parts based on pattern_colors
    for color, patterns in pattern_colors.items():
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                line = re.sub(pattern, lambda match: colored(match.group(), color), line, flags=re.IGNORECASE)

    # If the line contains a sound word, play a wav file
    if any(word in line for word in notify):
        current_time = time.time()
        if current_time - last_played > delay:
            winsound.PlaySound('sound.wav', winsound.SND_FILENAME)
            last_played = current_time

    # If the line contains a word from the word filter, return None
    if any(word in line for word in word_filter):
        return None
    return line
def colorize2(line):
    global last_played  # Use the global last_played variable
    # Process the line first
    processed_line = process_line(line, word_filter, notify)

    # If the processed line is None, return None
    if processed_line is None:
        return None

    # First, color the entire line based on color_patterns
    colored_line = processed_line
    for color, patterns in color_patterns.items():
        for pattern in patterns:
            if re.search(pattern, processed_line, re.IGNORECASE):
                colored_line = colored(processed_line, color)

    # Then, color the parts based on pattern_colors
    partially_colored_line = colored_line
    for color, patterns in pattern_colors.items():
        for pattern in patterns:
            if re.search(pattern, colored_line, re.IGNORECASE):
                partially_colored_line = re.sub(pattern, lambda match: colored(match.group(), color), colored_line, flags=re.IGNORECASE)

    # If the line contains a sound word, play a wav file
    if any(word in partially_colored_line for word in notify):
        current_time = time.time()
        if current_time - last_played > delay:
            winsound.PlaySound('sound.wav', winsound.SND_FILENAME)
            last_played = current_time

    # If the line contains a word from the word filter, return None
    if any(word in partially_colored_line for word in word_filter):
        return None
    return partially_colored_line

# The 'tail' function mimics the behavior of the Unix 'tail -f' command for a given file 'f'.
def tail(f):
    f.seek(0, os.SEEK_END)
    while True:
        line = f.readline()
        if not line:
            time.sleep(0.1)  # Sleep briefly
            continue
        yield line

# The 'process_line' function checks if a line contains any word from 'word_filter' or 'notify' lists.
# If a word from 'word_filter' is found, it returns None.
# If a word from 'notify' is found and 'mute' is False, it returns the line.
# If neither condition is met, it also returns None.
def process_line(line, word_filter, notify):
    # If the line contains a word from the word filter, return None
    if any(word in line for word in word_filter):
        return None

    # Check for "Stopping local server" before checking for notify words
    if "Stopping local server" in line:
        print(line)
        print("Exiting script...")
        sys.exit(0)

    # If the line contains a word from the notify list and mute is False, return the line
    if any(word in line for word in notify):
        return line

    return None

def format_date(line):
    # Split the line into entries
    entries = line.split('|')
    # Get the date string and remove leading/trailing whitespace
    date_string = entries[0].strip()
    # Parse the date string into a datetime object
    date = datetime.strptime(date_string, "%Y-%m-%d %H-%M-%S")
    # Format the datetime object into a more human-readable string
    formatted_date = date.strftime("%H:%M:%S")
    # Combine the formatted date with the rest of the line
    formatted_line = formatted_date + '> ' + ' '.join(entries[1:]).strip()

    return formatted_line

def check_and_exit(line):
    if "stopping local server" in line.lower():
        print(colorize("> Logfile closed, see you next time, spacehunk!", "light_cyan"))
        sys.exit(0)
# The 'main' function reads a file, stores the last 10 lines, and prints them. 
# It then continuously reads new lines from the file as they are written, colorizes them, and prints them.
# If a line contains a word from the 'notify' list, it is printed with a red background.
def main():
    # Open the file in UTF-8 encoding
    with open(path, 'r', encoding='utf-8') as f:
        # Create a deque to hold the last 10 lines
        last_10_lines = collections.deque((line.rstrip('\n') for line in f), 100)

    # Print the last 10 lines
    for line in last_10_lines:
        if line:  # Only print the line if it's not empty
            colored_line = colorize(format_date(line))  # Pass the color argument
            if colored_line:  # Only print the line if it's not None
                # Check if any notify word is in the colored_line
                if any(word in colored_line for word in notify):
                    # Change the background color and print
                    print(colored(colored_line, settings['notifycolor']['foreground'][0], settings['notifycolor']['background'][0]))
                else:
                    print(colored_line)
                # Check if the last entry is "stopping local server"
                check_and_exit(line)


    # Open the file and use tail to follow the file and get new lines as they are written
    with open(path, 'r', encoding='utf-8') as f:
        for line in tail(f):
            colored_line = colorize(line.rstrip('\n'))  # Pass the color argument
            check_and_exit(line)
            if colored_line:  # Only print the line if it's not None
                # Check if any notify word is in the colored_line
                if any(word in colored_line for word in notify):
                    # Change the background color to red and print
                    print(colored(colored_line, settings['notifycolor']['foreground'][0], settings['notifycolor']['background'][0]))
                else:
                    print(colored_line)

def main2():
    # Open the file in UTF-8 encoding
    with open(path, 'r', encoding='utf-8') as f:
        # Create a deque to hold the last 10 lines
        last_10_lines = collections.deque((line.rstrip('\n') for line in f), 100)

    # Print the last 10 lines
    for line in last_10_lines:
        colored_line = colorize(line)
        if colored_line:  # Only print the line if it's not None
            print(colored_line)

    # Open the file and use tail to follow the file and get new lines as they are written
    with open(path, 'r', encoding='utf-8') as f:
        for line in tail(f):
            colored_line = colorize(line.rstrip('\n'))
            if colored_line:  # Only print the line if it's not None
                print(colored_line)

if __name__ == "__main__":
    main()