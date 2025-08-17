import json
import os

PLAYLISTS_FILE = "playlists.json"

def load_playlists():
    if os.path.exists(PLAYLISTS_FILE):
        with open(PLAYLISTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_playlists(playlists):
    with open(PLAYLISTS_FILE, "w", encoding="utf-8") as f:
        json.dump(playlists, f, indent=4)

def create_playlist(name):
    playlists = load_playlists()
    if name in playlists:
        return False, "Playlist already exists."
    playlists[name] = []
    save_playlists(playlists)
    return True, f"Playlist '{name}' created."

def delete_playlist(name):
    playlists = load_playlists()
    if name not in playlists:
        return False, "Playlist not found."
    del playlists[name]
    save_playlists(playlists)
    return True, f"Playlist '{name}' deleted."

def rename_playlist(old_name, new_name):
    playlists = load_playlists()
    if old_name not in playlists:
        return False, "Original playlist not found."
    if new_name in playlists:
        return False, "New playlist name already exists."
    playlists[new_name] = playlists.pop(old_name)
    save_playlists(playlists)
    return True, f"Playlist renamed to '{new_name}'."

def add_song_to_playlist(playlist_name, song):
    playlists = load_playlists()
    if playlist_name not in playlists:
        return False, "Playlist not found."
    playlists[playlist_name].append(song)
    save_playlists(playlists)
    return True, f"Added '{song}' to '{playlist_name}'."

def remove_song_from_playlist(playlist_name, song):
    playlists = load_playlists()
    if playlist_name not in playlists or song not in playlists[playlist_name]:
        return False, "Song or playlist not found."
    playlists[playlist_name].remove(song)
    save_playlists(playlists)
    return True, f"Removed '{song}' from '{playlist_name}'."

def list_playlists():
    playlists = load_playlists()
    return list(playlists.keys())

def list_songs_in_playlist(name):
    playlists = load_playlists()
    return playlists.get(name, [])
