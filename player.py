# player.py
import vlc
import time
import os
from colorama import Fore, Style, init
from downloader import sanitize_filename, DOWNLOADS_DIR, download_song
from yt_dlp import YoutubeDL
import requests
import xml.etree.ElementTree as ET
from threading import Thread, Event, Lock
from favorites import load_favorites

init(autoreset=True)

# ------------------------------
# Utilities
# ------------------------------
def print_progress_bar(current, total, length=40):
    fraction = min(max(current / total, 0), 1)
    filled_length = int(length * fraction)
    bar = f"{Fore.GREEN}{'█'*filled_length}{Style.RESET_ALL}{'-'*(length - filled_length)}"
    print(f"\r⏱ {int(current)}/{int(total)} sec [{bar}]", end="", flush=True)  # overwrite same line

def fetch_yt_captions(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subs = info.get('subtitles') or info.get('automatic_captions') or {}
            en_sub = subs.get('en')
            if not en_sub:
                return []
            sub_url = en_sub[0]['url']
            r = requests.get(sub_url)
            lines = []
            root = ET.fromstring(r.text)
            for child in root.findall('.//text'):
                start = float(child.attrib.get('start', 0))
                text = "".join(child.itertext()).replace("\n", " ").strip()
                if text:
                    lines.append((start, text))
            return lines
    except:
        return []

def fetch_local_lyrics(file_path):
    base = os.path.splitext(file_path)[0]
    lrc_file = base + ".lrc"
    if not os.path.exists(lrc_file):
        return []
    lines = []
    with open(lrc_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and "]" in line:
                time_part = line[1:line.index("]")]
                try:
                    m, s = map(float, time_part.split(":"))
                    start = m*60 + s
                    text = line[line.index("]")+1:].strip()
                    lines.append((start, text))
                except:
                    continue
    return lines

def get_stream_url(song_name):
    """Return direct audio URL from YouTube for streaming without downloading"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song_name, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            return info['url'], info.get('title', song_name)
    except:
        return None, song_name

# ------------------------------
# Music Player Class
# ------------------------------
class MusicPlayer:
    def __init__(self):
        self.queue = []
        self.current_index = 0
        self.player = None
        self.lyrics_lines = []
        self.repeat = False
        self.paused = False
        self.stop_event = Event()
        self.lock = Lock()
        self.play_thread = None
        self.current_song = None
        self.lyrics_thread = None

    # --------------------------
    # Queue Management
    # --------------------------
    def add_to_queue(self, song, artist=None, stream=True):
        """Normal add (end of queue)"""
        with self.lock:
            self.queue.append((song, artist, stream))
            print(f"{Fore.CYAN}✅ Added to queue: {artist+' - ' if artist else ''}{song}{Style.RESET_ALL}")
        self._start_playback_if_needed()

    def insert_to_top(self, song, artist=None, stream=True):
        """Insert next (priority play)"""
        with self.lock:
            if not self.queue:
                self.queue.append((song, artist, stream))
                print(f"{Fore.CYAN}✅ Added to queue: {artist+' - ' if artist else ''}{song}{Style.RESET_ALL}")
            else:
                self.queue.insert(self.current_index + 1, (song, artist, stream))
                print(f"{Fore.CYAN}📌 Inserted next in queue: {artist+' - ' if artist else ''}{song}{Style.RESET_ALL}")
        self.stop_event.set()
        self._start_playback_if_needed()

    def _start_playback_if_needed(self):
        if not self.play_thread or not self.play_thread.is_alive():
            self.play_thread = Thread(target=self.play_current, daemon=True)
            self.play_thread.start()

    def show_queue(self):
        favorites = load_favorites()
        if not self.queue:
            print(f"{Fore.YELLOW}⚠ Queue is empty.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.MAGENTA}🎵 Current Queue:{Style.RESET_ALL}")
        for i, (song, artist, _) in enumerate(self.queue):
            marker = f"{Fore.GREEN}▶️ " if i == self.current_index else "   "
            marker += f"{Fore.MAGENTA}★ " if song in favorites else "  "
            print(f"{marker}{i+1}. {artist+' - ' if artist else ''}{song}")

    # --------------------------
    # Playback
    # --------------------------
    def play_current(self):
        while self.current_index < len(self.queue):
            song, artist, stream = self.queue[self.current_index]

            if stream:
                audio_url, song_title = get_stream_url(song)
                if not audio_url:
                    print(f"{Fore.RED}❌ Failed to stream: {song}{Style.RESET_ALL}")
                    self.current_index += 1
                    continue
                media_source = audio_url
                self.lyrics_lines = fetch_yt_captions(audio_url)
                display_name = song_title
            else:
                media_source = song
                self.lyrics_lines = fetch_local_lyrics(song)
                display_name = song

            self.current_song = display_name
            print(f"\n{Fore.CYAN}🎶 Now Playing: {artist+' - ' if artist else ''}{display_name}{Style.RESET_ALL}\n")

            self.player = vlc.MediaPlayer(media_source)
            self.player.play()
            self.paused = False
            time.sleep(1)
            duration_ms = self.player.get_length()
            duration_sec = duration_ms / 1000 if duration_ms > 0 else 10
            start_time = time.time()

            # launch lyrics thread
            if self.lyrics_lines:
                self.lyrics_thread = Thread(target=self._sync_lyrics, args=(start_time,), daemon=True)
                self.lyrics_thread.start()

            while self.player.get_state() != vlc.State.Ended:
                if self.stop_event.is_set():
                    self.player.stop()
                    self.stop_event.clear()
                    break

                if self.paused:
                    time.sleep(0.5)
                    start_time += 0.5
                    continue

                elapsed = time.time() - start_time
                print(f"\r🎵 {artist+' - ' if artist else ''}{display_name} | {int(elapsed)}s/{int(duration_sec)}s", end="", flush=True)
                time.sleep(1)

            print()  # ensure newline when song ends
            with self.lock:
                if self.repeat:
                    continue
                self.current_index += 1

        self.current_song = None

    def _sync_lyrics(self, start_time):
        """Print lyrics in sync with elapsed time"""
        for ts, line in self.lyrics_lines:
            while True:
                elapsed = time.time() - start_time
                if elapsed >= ts:
                    print(f"\n{Fore.MAGENTA}🎤 {line}{Style.RESET_ALL}")
                    break
                time.sleep(0.2)

    # --------------------------
    # Controls
    # --------------------------
    def next_song(self):
        with self.lock:
            if self.current_index + 1 < len(self.queue):
                self.current_index += 1
                self.stop_event.set()
            else:
                print(f"{Fore.CYAN}✅ Reached end of queue.{Style.RESET_ALL}")

    def prev_song(self):
        with self.lock:
            if self.current_index > 0:
                self.current_index -= 1
                self.stop_event.set()
            else:
                print(f"{Fore.YELLOW}⚠ Already at first song.{Style.RESET_ALL}")

    def skip(self):
        self.stop_event.set()

    def pause(self):
        if self.player and not self.paused:
            self.player.pause()
            self.paused = True
            print(f"\n{Fore.CYAN}⏸ Paused{Style.RESET_ALL}")

    def resume(self):
        if self.player and self.paused:
            self.player.pause()
            self.paused = False
            print(f"\n{Fore.CYAN}▶ Resumed{Style.RESET_ALL}")

    def show_lyrics(self):
        """Force print all lyrics at once (non-synced mode)"""
        if not self.lyrics_lines:
            print(f"{Fore.RED}❌ No lyrics available.{Style.RESET_ALL}")
            return
        print(f"\n{Fore.MAGENTA}🎤 Lyrics:{Style.RESET_ALL}")
        for _, line in self.lyrics_lines:
            print(line)
