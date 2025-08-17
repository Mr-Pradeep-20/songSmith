# artist_limit.py
import json
import os
from datetime import date, datetime, timedelta
import threading
import time
from colorama import Fore, Style

DATA_FILE = "artist_limit.json"
HISTORY_FILE = "downloaded_songs.json"

MAX_ARTISTS_PER_DAY = 3
MAX_SONGS_PER_ARTIST = 10

data_lock = threading.Lock()

# ------------------------------
# Load/save limit data
# ------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            if "date" not in data:
                data["date"] = str(date.today())
            if "artists" not in data:
                data["artists"] = {}
            return data
        except json.JSONDecodeError:
            return {"date": str(date.today()), "artists": {}}
    return {"date": str(date.today()), "artists": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ------------------------------
# Load/save song history
# ------------------------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

# ------------------------------
# Time until daily reset
# ------------------------------
def time_until_reset():
    now = datetime.now()
    tomorrow = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
    remaining = tomorrow - now
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes = remainder // 60
    return f"{hours}h {minutes}m"

# ------------------------------
# Reset limits daily
# ------------------------------
def reset_if_new_day(data):
    today_str = str(date.today())
    if data.get("date") != today_str:
        data["date"] = today_str
        data["artists"] = {}
        save_history([])
        print(f"\n{Fore.CYAN}🔄 Daily limits reset!{Style.RESET_ALL}\n")
    return data

# ------------------------------
# Check if download allowed
# ------------------------------
def can_download_artist(artist_name, song_title=None):
    """
    Checks daily limits for artist and song.
    Returns (allowed: bool, message_or_remaining: str/int)
    """
    with data_lock:
        data = load_data()
        data = reset_if_new_day(data)

        artist_name_lower = artist_name.lower()

        # Limit max 3 artists per day
        if artist_name_lower not in data["artists"] and len(data["artists"]) >= MAX_ARTISTS_PER_DAY:
            save_data(data)
            return False, (
                f"{Fore.RED}🚫 Maximum of {MAX_ARTISTS_PER_DAY} different artists reached today.{Style.RESET_ALL}\n"
                f"{Fore.CYAN}⏳ Time until reset: {time_until_reset()}{Style.RESET_ALL}\n"
                f"{Fore.MAGENTA}🙏 Thank you for using SongSmith!{Style.RESET_ALL}"
            )

        # Limit max 10 songs per artist
        current_count = data["artists"].get(artist_name_lower, 0)
        if current_count >= MAX_SONGS_PER_ARTIST:
            save_data(data)
            return False, (
                f"{Fore.RED}🚫 Already downloaded {MAX_SONGS_PER_ARTIST} songs for '{artist_name}' today.{Style.RESET_ALL}\n"
                f"{Fore.CYAN}⏳ Time until reset: {time_until_reset()}{Style.RESET_ALL}\n"
                f"{Fore.MAGENTA}🙏 Thank you for using SongSmith!{Style.RESET_ALL}"
            )

        # Prevent duplicate song downloads
        if song_title:
            history = load_history()
            if song_title.lower() in [s.lower() for s in history]:
                return False, f"{Fore.YELLOW}⚠ Song '{song_title}' already downloaded.{Style.RESET_ALL}"

        # Update counts and history
        data["artists"][artist_name_lower] = current_count + 1
        save_data(data)

        if song_title:
            history = load_history()
            history.append(song_title)
            save_history(history)

        remaining = MAX_SONGS_PER_ARTIST - data["artists"][artist_name_lower]
        return True, remaining

# ------------------------------
# Background thread to reset limits daily
# ------------------------------
def daily_reset_checker():
    while True:
        with data_lock:
            data = load_data()
            updated_data = reset_if_new_day(data)
            save_data(updated_data)
        time.sleep(60)  # check every minute

# Start background reset thread
threading.Thread(target=daily_reset_checker, daemon=True).start()
