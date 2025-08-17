# downloader.py
import os
import yt_dlp
from colorama import Fore, Style
from artist_limit import can_download_artist, load_history, save_history
from lyrics import fetch_lyrics  # <-- Auto-fetch lyrics

DOWNLOADS_DIR = "downloads"

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in " -_").strip()

def download_song(query, artist=None, limit=1):
    artist_folder = sanitize_filename(artist) if artist else "Misc"
    save_path = os.path.join(DOWNLOADS_DIR, artist_folder)
    os.makedirs(save_path, exist_ok=True)

    ydl_opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "noplaylist": True,
        "outtmpl": os.path.join(save_path, "%(title)s.%(ext)s"),
    }

    if artist:
        ydl_opts["playlistend"] = limit

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)

        entries = info.get("entries", [info])
        entries = [e for e in entries if e]  # remove None
        entries.sort(key=lambda x: x.get("view_count", 0), reverse=True)

        for entry in entries[:limit]:
            song_title = entry.get("title", "Unknown Song")
            file_ext = entry.get("ext", "webm")
            song_file = os.path.join(save_path, f"{sanitize_filename(song_title)}.{file_ext}")

            # Check daily limits & duplicates
            allowed, message = can_download_artist(artist or song_title, song_title)
            if not allowed:
                print(f"{Fore.RED}{message}{Style.RESET_ALL}")
                continue

            # Skip if file already exists
            if os.path.exists(song_file):
                print(f"{Fore.YELLOW}⚠ '{song_title}' already exists — skipping.{Style.RESET_ALL}")
                continue

            # Download the song
            print(f"{Fore.CYAN}⬇ Downloading: {song_title}{Style.RESET_ALL}")
            ydl.download([entry["webpage_url"]])

            # Save to history
            history = load_history()
            if song_title.lower() not in [s.lower() for s in history]:
                history.append(song_title)
                save_history(history)

            # Auto-fetch and display lyrics
            lyrics_text = fetch_lyrics(song_title, artist)
            print(lyrics_text)
