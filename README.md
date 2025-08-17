🎵 SongSmith

A CLI-based Music Player built with Python
A command-line music player that lets you play, download, and manage music right from your terminal.
It supports local playback, YouTube downloads, favorites, and real-time CLI controls with full cross-platform support (Windows & Linux).

🚀 Features

🎧 Play local audio files directly in the terminal

⬇️ Download songs from YouTube using yt-dlp

❤️ Add and manage favorite tracks

⏯️ Playback controls: play, pause, stop, next, previous

📂 Organizes music in a Downloads directory automatically

🌐 Works on Windows and Linux

⚡ Fast and lightweight (powered by VLC backend)


🛠️ Tech Stack & Dependencies

This project is built with Python 3.8+ and uses the following packages:

python-vlc → Music playback

yt-dlp → Download YouTube audio

requests → Handle API/web requests

colorama → Colored CLI output

threading → Non-blocking playback

xml.etree.ElementTree → XML parsing (for feeds, optional)

🔑 Requirement: VLC Media Player must be installed (the vlc Python module depends on it).


📂 Project Structure

songsmith/
│── player.py         # Core player logic (VLC-based playback)

│── downloader.py     # Download logic (YouTube, sanitization, downloads folder)

│── favorites.py      # Favorites system (add/remove/load favorites)

│── lyrics.py         # Lyrics fetcher using Genius API

│── main.py           # Entry point - CLI interface

│── requirements.txt  # Dependencies list

│── README.md         # Project documentation

│── Downloads/        # Downloaded music files

│── lyrics_cache/     # Cached lyrics


⚙️ Installation

🪟 Windows

Install Python 3.8+ → Download here

Install VLC Media Player → Download here

Clone this repository:

git clone https://github.com/Mr-Pradeep-20/songsmith.git

cd songsmith

Install dependencies:

pip install -r requirements.txt\

Run the project:

python main.py

🐧 Linux

Install Python (if not installed):

sudo apt update && sudo apt install python3 python3-pip -y

Install VLC:

sudo apt install vlc -y

Clone this repository:

git clone https://github.com/Mr-Pradeep-20/songsmith.git

cd songsmith

Install dependencies:

pip3 install -r requirements.txt

Run the project:

python3 main.py

📌 Usage

Once you run main.py, you’ll see the CLI menu:

Welcome to SongSmith 🎶

1. Play a local file

3. Play a song from YouTube
  
5. Download a song
   
7. Show Favorites
  
9. Add to Favorites
    
11. Show Lyrics
    
13. Exit


Select 1 → Play local songs

Select 2 → Stream from YouTube

Select 3 → Download a song

Select 4 → List your favorites

Select 5 → Add a song to favorites

Select 6 → Fetch lyrics (from Genius API)

Select 7 → Exit


💡 Use Cases

Minimalist music player without a heavy GUI

Quickly download & play YouTube songs

Keep a personal favorites playlist

Works well on low-resource systems (terminal-based)

Extendable for shuffle, loop, or playlist management


⚠️ Notes

Works best with .mp3 and .wav formats

Ensure VLC is installed and available in system PATH

Requires internet connection for YouTube streaming & lyrics

Lyrics are cached locally in lyrics_cache/


📝 License

This project is open-source under the MIT License.
