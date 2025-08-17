# main.py
import os
import time
import json
import random
import threading
import sys
from colorama import Fore, Style, init
from pyfiglet import Figlet

from player import MusicPlayer
from downloader import download_song
from artist_limit import can_download_artist
from lyrics import fetch_lyrics
from favorites import add_favorite, remove_favorite, load_favorites
import yt_dlp

init(autoreset=True)

# ------------------------------
# Playlist management
# ------------------------------
PLAYLIST_FILE = "playlists.json"

def load_playlists():
    if not os.path.exists(PLAYLIST_FILE):
        return {}
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_playlists(playlists):
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(playlists, f, indent=4)

def create_playlist(name):
    playlists = load_playlists()
    if name in playlists:
        return False
    playlists[name] = []
    save_playlists(playlists)
    return True

def delete_playlist(name):
    playlists = load_playlists()
    if name in playlists:
        del playlists[name]
        save_playlists(playlists)
        return True
    return False

def rename_playlist(old_name, new_name):
    playlists = load_playlists()
    if old_name in playlists and new_name not in playlists:
        playlists[new_name] = playlists.pop(old_name)
        save_playlists(playlists)
        return True
    return False

def add_song_to_playlist(playlist, song):
    playlists = load_playlists()
    if playlist not in playlists:
        return False
    playlists[playlist].append(song)
    save_playlists(playlists)
    return True

def remove_song_from_playlist(playlist, song):
    playlists = load_playlists()
    if playlist not in playlists:
        return False
    if song in playlists[playlist]:
        playlists[playlist].remove(song)
        save_playlists(playlists)
        return True
    return False

def list_playlists():
    playlists = load_playlists()
    return list(playlists.keys())

def list_songs_in_playlist(name):
    playlists = load_playlists()
    return playlists.get(name, [])

# ------------------------------
# Utilities (YouTube helpers)
# ------------------------------
def get_top_songs(artist_name, limit=10):
    query = f"ytsearch{limit}:{artist_name}"
    ydl_opts = {"quiet": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        entries = info.get("entries", [info])
        entries = [e for e in entries if e]
        entries.sort(key=lambda x: x.get("view_count", 0), reverse=True)
        return [(e.get("title", "Unknown Song"), e.get("webpage_url")) for e in entries[:limit]]

def get_similar_songs(song_name, limit=5):
    query = f"ytsearch{limit}:{song_name}"
    ydl_opts = {"quiet": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            entries = info.get("entries", [])
            entries = [e for e in entries if e]
            entries.sort(key=lambda x: x.get("view_count", 0), reverse=True)
            return [(e.get("title", "Unknown Song"), e.get("webpage_url")) for e in entries[:limit]]
        except Exception:
            return []

def show_favorites_with_index():
    favorites = load_favorites()
    if favorites:
        print(f"\n{Fore.CYAN}🎵 Your Favorite Songs ({len(favorites)}):{Style.RESET_ALL}")
        for i, song in enumerate(favorites, 1):
            print(f"{i}. {song}")
    else:
        print(f"{Fore.YELLOW}⚠ You have no favorite songs yet.{Style.RESET_ALL}")

# ------------------------------
# Banner and Help
# ------------------------------
def show_banner():
    os.system('cls' if os.name=='nt' else 'clear')
    f = Figlet(font='slant')
    print(Fore.GREEN + f.renderText("SongSmith") + Style.RESET_ALL)
    print(Fore.CYAN + "Type 'help' to see available commands\n" + Style.RESET_ALL)

def show_help():
    print(Fore.CYAN + "=== Core Playback Commands ===" + Style.RESET_ALL)
    print("play <query>            : Add to queue (starts if idle)")
    print("add <query>             : Add to queue without interrupting")
    print("insert <query>          : Add song to play next")
    print("next / prev             : Navigate songs")
    print("pause / resume          : Control playback")
    print("repeat                  : Toggle repeat")
    print("queue                   : Show current queue\n")

    print(Fore.YELLOW + "=== Download Commands ===" + Style.RESET_ALL)
    print("download <query or url>       : Download a single song")
    print("download artist:<name>        : Download top songs from artist\n")

    print(Fore.MAGENTA + "=== Playlist Commands ===" + Style.RESET_ALL)
    print("pl create <name>              : Create a playlist")
    print("pl delete <name>              : Delete a playlist")
    print("pl rename <old> <new>         : Rename a playlist")
    print("pl add <pl> <song>            : Add song to playlist")
    print("pl remove <pl> <song>         : Remove song from playlist")
    print("pl list                       : List all playlists")
    print("pl songs <name>               : List songs in a playlist")
    print("pl play <name>                : Enqueue a playlist (choose order)\n")

    print(Fore.GREEN + "=== Favorites / Lyrics ===" + Style.RESET_ALL)
    print("fav add <song>                : Add song to favorites")
    print("fav remove <song>             : Remove from favorites")
    print("fav list                      : Show all favorites")
    print("playfav <index>               : Play favorite by index")
    print("playallfav                    : Play all favorites")
    print("lyrics <song>                 : Show lyrics (static)\n")

    print(Fore.CYAN + "=== Misc ===" + Style.RESET_ALL)
    print("help, exit")

# ------------------------------
# Now Playing Display (non-blocking, no refresh spam)
# ------------------------------
def now_playing_display(player: MusicPlayer):
    """
    Prints a single 'Now Playing' line whenever the song changes.
    Does NOT clear screen or overwrite the input line aggressively.
    """
    last_song = None
    while True:
        try:
            if getattr(player, "current_song", None) and player.current_song != last_song:
                last_song = player.current_song
                # Add newlines so it doesn't overwrite the input line
                sys.stdout.write(f"\n{Fore.MAGENTA}🎶 Now Playing: {last_song}{Style.RESET_ALL}\n\n")
                sys.stdout.flush()
        except Exception:
            pass
        time.sleep(1)

# ------------------------------
# Main CLI
# ------------------------------
def main():
    player = MusicPlayer()
    # Ensure the attribute exists from the start for the display thread
    if not hasattr(player, "current_song"):
        player.current_song = None

    show_banner()

    # Start Now Playing notifier thread
    threading.Thread(target=now_playing_display, args=(player,), daemon=True).start()

    while True:
        try:
            command = input(Fore.GREEN + "\nSongSmith > " + Style.RESET_ALL).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break

        if not command:
            continue

        if command.lower() == "exit":
            print("\n👋 Goodbye!")
            break
        if command.lower() == "help":
            show_help()
            continue

        try:
            exec_existing_commands(command, player)
        except Exception as e:
            print(Fore.RED + f"⚠ Error: {e}" + Style.RESET_ALL)

# ------------------------------
# Command execution
# ------------------------------
def exec_existing_commands(command, player: MusicPlayer):
    cmd = command.strip()

    # ---------- Playlist Commands (short 'pl' syntax) ----------
    if cmd.lower().startswith("pl "):
        parts = cmd.split()
        action = parts[1].lower() if len(parts) > 1 else ""

        if action == "create" and len(parts) >= 3:
            ok = create_playlist(parts[2])
            print("✅ Created." if ok else "⚠ Playlist already exists.")
        elif action == "delete" and len(parts) >= 3:
            ok = delete_playlist(parts[2])
            print("✅ Deleted." if ok else "⚠ Playlist not found.")
        elif action == "rename" and len(parts) >= 4:
            ok = rename_playlist(parts[2], parts[3])
            print("✅ Renamed." if ok else "⚠ Rename failed.")
        elif action == "add" and len(parts) >= 4:
            playlist_name = parts[2]
            song_name = " ".join(parts[3:])
            ok = add_song_to_playlist(playlist_name, song_name)
            print("✅ Added." if ok else "⚠ Add failed (playlist?).")
        elif action == "remove" and len(parts) >= 4:
            playlist_name = parts[2]
            song_name = " ".join(parts[3:])
            ok = remove_song_from_playlist(playlist_name, song_name)
            print("✅ Removed." if ok else "⚠ Remove failed.")
        elif action == "list":
            pls = list_playlists()
            if pls:
                print("\n🎵 Playlists:")
                for p in pls:
                    print(f"- {p} ({len(list_songs_in_playlist(p))} songs)")
            else:
                print("⚠ No playlists found.")
        elif action == "songs" and len(parts) >= 3:
            plname = parts[2]
            songs = list_songs_in_playlist(plname)
            if songs:
                print(f"\n🎼 Songs in '{plname}':")
                for i, s in enumerate(songs, 1):
                    print(f"{i}. {s}")
            else:
                print(f"⚠ Playlist '{plname}' is empty or not found.")
        elif action == "play" and len(parts) >= 3:
            plname = parts[2]
            songs = list_songs_in_playlist(plname)
            if not songs:
                print(f"⚠ Playlist '{plname}' is empty or does not exist.")
                return
            print("Select play method: 1) start-to-end  2) random  3) by name")
            method = input("> ").strip()
            if method == "1":
                for s in songs:
                    player.add_to_queue(s, stream=True)
            elif method == "2":
                shuffled = songs[:]
                random.shuffle(shuffled)
                for s in shuffled:
                    player.add_to_queue(s, stream=True)
            elif method == "3":
                name = input("Enter the song name from the playlist: ").strip()
                if name in songs:
                    player.add_to_queue(name, stream=True)
                else:
                    print("⚠ Not found in playlist.")
            else:
                for s in songs:
                    player.add_to_queue(s, stream=True)
        else:
            print("⚠ Usage: pl [create|delete|rename|add|remove|list|songs|play] ...")
        return

    # ---------- Core Playback (friendly commands) ----------
    low = cmd.lower()
    if low.startswith("play "):
        # Enqueue; playback thread will auto-start if idle
        player.add_to_queue(cmd[5:].strip(), stream=True)
        return
    if low.startswith("add "):
        # Explicit alias to add to queue without interrupting
        player.add_to_queue(cmd[4:].strip(), stream=True)
        return
    if low.startswith("insert "):
        player.insert_to_top(cmd[7:].strip(), stream=True)
        return
    if low in ("next", "n", "s*next"):
        player.next_song()
        return
    if low in ("prev", "p", "s*prev"):
        player.prev_song()
        return
    if low in ("pause", "s*pause"):
        player.pause()
        return
    if low in ("resume", "s*resume"):
        player.resume()
        return
    if low in ("repeat", "s*repeat"):
        player.repeat = not player.repeat
        print(f"{Fore.CYAN}🔁 Repeat is now {'ON' if player.repeat else 'OFF'}{Style.RESET_ALL}")
        return
    if low in ("queue", "s*queue"):
        player.show_queue()
        return

    # ---------- Favorites ----------
    if low.startswith("fav "):
        # fav add <song> | fav remove <song> | fav list
        parts = cmd.split(maxsplit=2)
        if len(parts) == 2 and parts[1].lower() == "list":
            show_favorites_with_index()
            return
        if len(parts) >= 3:
            action = parts[1].lower()
            song = parts[2].strip()
            if action == "add":
                add_favorite(song)
                print("⭐ Added to favorites.")
            elif action == "remove":
                remove_favorite(song)
                print("🗑️ Removed from favorites.")
            else:
                print("⚠ Usage: fav [add|remove|list] <song?>")
            return
        print("⚠ Usage: fav [add|remove|list] <song?>")
        return

    if low == "fav list" or low == "favorites" or low == "s*favlist":
        show_favorites_with_index()
        return

    if low.startswith("playfav "):
        index_str = cmd.split(maxsplit=1)[1].strip()
        if index_str.isdigit():
            idx = int(index_str) - 1
            favorites = load_favorites()
            if 0 <= idx < len(favorites):
                player.add_to_queue(favorites[idx], stream=True)
            else:
                print("⚠ Index out of range.")
        else:
            print("⚠ Usage: playfav <index>")
        return

    if low == "playallfav" or low == "s*playallfav":
        favorites = load_favorites()
        if not favorites:
            print("⚠ No favorites yet.")
        for s in favorites:
            player.add_to_queue(s, stream=True)
        return

    # ---------- Downloads ----------
    if low.startswith("download "):
        song_or_artist = cmd[9:].strip()
        if song_or_artist.lower().startswith("artist:"):
            artist_name = song_or_artist[7:].strip()
            if not artist_name:
                print(f"{Fore.YELLOW}⚠ Please provide an artist name.{Style.RESET_ALL}")
                return
            allowed, msg = can_download_artist(artist_name)
            if not allowed:
                print(f"{Fore.RED}{msg}{Style.RESET_ALL}")
                return
            top_songs = get_top_songs(artist_name)
            if not top_songs:
                print("⚠ No results.")
                return
            print(f"\n{Fore.CYAN}🎵 Top {len(top_songs)} songs for '{artist_name}':{Style.RESET_ALL}")
            for i, (title, _) in enumerate(top_songs, 1):
                print(f"{i}. {title}")
            user_input = input(f"{Fore.CYAN}Type numbers separated by comma or 'all': {Style.RESET_ALL}").strip().lower()
            if user_input == "all":
                selected = top_songs
            else:
                idxs = [int(x)-1 for x in user_input.split(",") if x.strip().isdigit()]
                selected = [top_songs[i] for i in idxs if 0 <= i < len(top_songs)]
            for title, url in selected:
                download_song(url, artist=artist_name)
        else:
            # Download a single song by query or URL
            download_song(song_or_artist)
        return

    # ---------- Lyrics ----------
    if low.startswith("lyrics "):
        print(fetch_lyrics(cmd[7:].strip()))
        return

    # ---------- Back-compat (old s* commands) ----------
    if low.startswith("s*play "):
        player.add_to_queue(cmd[7:].strip(), stream=True)
        return
    if low.startswith("s*insert "):
        player.insert_to_top(cmd[9:].strip(), stream=True)
        return

    # ---------- Unknown ----------
    print(Fore.YELLOW + "❓ Unknown command. Type 'help' for the list of commands." + Style.RESET_ALL)

# ------------------------------
# Run
# ------------------------------
if __name__ == "__main__":
    main()
