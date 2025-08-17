# favorites.py
import json
import os
from colorama import Fore, Style

FAV_FILE = "favorites.json"

def load_favorites():
    if os.path.exists(FAV_FILE):
        try:
            with open(FAV_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_favorites(favorites):
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)

def add_favorite(song_name, url=None):
    favorites = load_favorites()
    if song_name.lower() not in [s['name'].lower() for s in favorites]:
        favorites.append({"name": song_name, "url": url})
        save_favorites(favorites)
        print(f"{Fore.GREEN}❤️ '{song_name}' added to favorites!{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠ '{song_name}' is already in favorites.{Style.RESET_ALL}")

def remove_favorite(song_name):
    favorites = load_favorites()
    new_favs = [s for s in favorites if s['name'].lower() != song_name.lower()]
    if len(new_favs) != len(favorites):
        save_favorites(new_favs)
        print(f"{Fore.GREEN}💔 '{song_name}' removed from favorites.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠ '{song_name}' was not in favorites.{Style.RESET_ALL}")

def list_favorites():
    favorites = load_favorites()
    if not favorites:
        print(f"{Fore.CYAN}💡 No favorite songs yet.{Style.RESET_ALL}")
        return
    print(f"{Fore.CYAN}🎵 Favorite Songs:{Style.RESET_ALL}")
    for i, s in enumerate(favorites, 1):
        print(f"{i}. {s['name']}")
