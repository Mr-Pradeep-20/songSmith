# lyrics.py
import lyricsgenius
from colorama import Fore, Style
import os
import json

# Genius API token
GENIUS_API_TOKEN = "UL9ZrMqVcTQ8oSdjSKrit4U3s5USdCieRHAvU_kuOnRDsX_vGf2g8MEL3PNX35xC"

genius = lyricsgenius.Genius(
    GENIUS_API_TOKEN,
    skip_non_songs=True,
    excluded_terms=["Remix", "Live"],
    remove_section_headers=True,
    timeout=15
)

CACHE_DIR = "lyrics_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(song_name, artist_name=None):
    safe_name = f"{song_name}_{artist_name}" if artist_name else song_name
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in " -_").strip()
    return os.path.join(CACHE_DIR, f"{safe_name}.json")

def fetch_lyrics(song_name, artist_name=None):
    """
    Fetch lyrics for a given song, optionally by artist.
    Uses local cache if available.
    :param song_name: Name of the song
    :param artist_name: Optional artist name
    :return: Lyrics string or a message if not found
    """
    cache_file = _cache_path(song_name, artist_name)

    # Check cache first
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return f"\n{Fore.CYAN}🎵 Lyrics for '{data.get('title','Unknown')}':{Style.RESET_ALL}\n\n{data.get('lyrics','')}"
        except:
            pass  # ignore cache errors and fetch fresh

    # Fetch from Genius API
    try:
        song = genius.search_song(song_name, artist_name) if artist_name else genius.search_song(song_name)
        if song and song.lyrics:
            # Save to cache
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump({"title": song.title, "lyrics": song.lyrics}, f, ensure_ascii=False, indent=2)
            except:
                pass  # ignore cache save errors
            return f"\n{Fore.CYAN}🎵 Lyrics for '{song.title}':{Style.RESET_ALL}\n\n{song.lyrics}"
        else:
            return f"{Fore.YELLOW}⚠ Lyrics not found for '{song_name}'.{Style.RESET_ALL}"
    except Exception as e:
        return f"{Fore.RED}❌ Error fetching lyrics: {e}{Style.RESET_ALL}"
