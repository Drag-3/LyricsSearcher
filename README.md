# Lyrics Searcher

Lyrics Searcher is a Python tool that allows users to search for song lyrics. It provides both single and batch modes for searching and retrieving lyrics.

## Features

- Search for song lyrics by track name and artist
- Search for song lyrics using a Spotify URL
- Search for song lyrics using a Spotify track ID
- Search for song lyrics by the path to an audio file
- Get output in LRC format if available
- Get lyrics files in TXT format (batch mode)

## Prerequisites

Before using this tool, make sure you have the following:

- Python 3.6 or above installed on your system
- The required dependencies listed in the 'requirements.txt' file
- A Genius [access token](http://genius.com/api-clients)
- The Value of the sp_dc cookie 

### How to find sp_dc
1. Log into spotify on the browser of your choice, preferably in Incognito mode.
2. Enter (Dev Mode) for your browser
3. Find Cookie Storage, and the sp_dc cookie
4. You Have Found It !
- NOTE: if you log out of spotify in the session you will need to regenerate the token. Close the tab/window without logging out in order to extend the life of the cookie.

## Installation

### Basic Installation
To install and use the project normally:
1. Install the project with pip:

   ```bash
    pip install git+https://github.com/Drag-3/LyricsSearcher.git 
    ```

### Dev Installation
To install the project for testing or modification
1. Clone this repository:
   ```bash
   git clone https://github.com/Drag-3/LyricsSearcher.git
    ```
2. Navigate to the cloned repo
    ```bash
   cd LyricsSearcher
    ```
3. Install Required Dependencies
    ```bash
   pip install -r requirements.txt
    ```

## Usage

To use the Song Lyrics Search tool, follow the instructions below.

### Single Mode

In single mode, you can search for song lyrics for a single track. You can use output redirection to move the lyrics into a file.

#### Search by Track Name and Artist

To search for song lyrics by track name and artist, use the following command:

` lyrics [-y] single artist <track_name> <track_artist>`

Replace '<track_name>' with the name of the track and '<track_artist>' with the name of the artist. The `-y` option does not work for this mode.

#### Search by Spotify URL

To search for song lyrics using a Spotify URL, use the following command:

` lyrics [-y] single spotify_url <spotify_url> `

Replace '<spotify_url>' with the Spotify URL of the track. Use the `-y` option to get the output in LRC format if available.

#### Search by Spotify Track ID

To search for song lyrics using a Spotify track ID, use the following command:

` lyrics [-y] single spotify_id <spotify_track_id> `

Replace '<spotify_track_id>' with the Spotify track ID. Use the `-y` option to get the output in LRC format if available.

#### Search by File

To search for song lyrics by the path to an audio file, use the following command:

` lyrics [-y] single file <file_path> `

Replace '<file_path>' with the path to the audio file. Use the `-y` option to get the output in LRC format if available.

### Batch Mode

In batch mode, you can search for song lyrics for multiple files in a directory.

` lyrics batch [-t] <search_path>`

Replace '<search_path>' with the path to the directory containing the audio files. In batch lrc format is the default mode. Use the `-t` option to get the lyrics files in TXT format instead of LRC format.

### Auth Mode

In auth mode you can set and get the credentials used for spotify and the genius api

#### Set

` lyrics auth set <service> <token> `

Replace `<service` with the actual service, i.e. `spotify` and `token` with the token to Save

#### Get

` lyrics auth get <service> `

Replace `<service` with the actual service

### Examples

Here are some examples of how to use Lyrics Searcher:

- Search for lyrics by track name and artist:

  ```bash
    lyrics single artist "Believer" "Imagine Dragons" 
    ```

- Search for lyrics using a Spotify URL:

  ```bash
    lyrics single spotify_url "https://open.spotify.com/track/3d8YuvVzSlLnfnEssaGGL7"
    ```

- Search for lyrics using a Spotify track ID and get lrc lyrics if available:

  ```bash 
  lyrics -y single spotify_id "3d8YuvVzSlLnfnEssaGGL7"
   ```
  
- Search a directory for lyrics, creating a lyrics file for each valid music file:

    ```bash
  lyrics batch "/home/Mayo/Music"
   ```
  
## Use as Module

The lyrics_searcher.api module defines convince functions to use the LyricsSearcher class. The credentials must be saved before use.
```python3
import pathlib
from lyrics_searcher import api, auth

auth.save_auth('spotify', "token")
auth.save_auth('genius', "token")

lyrics_type, lyrics = api.search_lyrics_by_file(pathlib.Path("Path to file"), lrc=True)

lyrics1 = api.search_lyrics_by_name_artist("Title", "Artist")

lyrics_type2, lyrics2 = api.search_lyrics_by_spotify_track_id("Track ID")

lyrics_type3, lyrics3 = api.search_lyrics_by_spotify_url("Spotify Url")

```
If you need to configure the LyricsSearcher object you can import the lyrics_finder module and directly create the object
```python3
from lyrics_searcher import lyric_finder
searcher = lyric_finder.LyricsSearcher("Spotify sp_dc", "Genius Access Token")

searcher.get_spotify_lyrics(t_url="Url")
```

## License
Lyrics Searcher is licensed under the GPL-3.0 license.