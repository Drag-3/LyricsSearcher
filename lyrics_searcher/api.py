import logging
import threading
from pathlib import Path

from lyrics_searcher.auth import get_auth
from lyrics_searcher.utils import Tagger
from lyrics_searcher.utils import Track
from lyrics_searcher.lyric_finder import LyricsSearcher


def search_lyrics_by_name_artist(track_name, track_artist):
    spdc = get_auth("spotify")
    g_tok = get_auth("genius")
    lyrics_searcher = LyricsSearcher(spdc, g_tok)

    track = Track(track_name=track_name, track_artists=[track_artist])
    return lyrics_searcher.get_genius_lyrics(track)


def search_lyrics_by_spotify_url(spotify_url, track_info=None, lrc=False):
    spdc = get_auth("spotify")
    g_tok = get_auth("genius")
    lyrics_searcher = LyricsSearcher(spdc, g_tok)

    return lyrics_searcher.get_spotify_lyrics(t_url=spotify_url, track_info=track_info, lrc=lrc)


def search_lyrics_by_spotify_track_id(track_id, track_info=None, lrc=False):
    spdc = get_auth("spotify")
    g_tok = get_auth("genius")
    lyrics_searcher = LyricsSearcher(spdc, g_tok)

    return lyrics_searcher.get_spotify_lyrics(t_id=track_id, track_info=track_info, lrc=lrc)


def search_lyrics_by_file(music_file: Path, lrc=False):
    # Extract track metadata from the music file and search for lyrics
    track = extract_info_from_file(music_file)

    if not track:
        logging.warning(f"Failed to extract track metadata from: {music_file}")
        return None, None

    if not track.track_url or 'https://open.spotify.com/track/' not in track.track_url:
        source_type = 'genius'
    else:
        source_type = 'spotify'

    result = None
    lyric_type = None
    if source_type == 'spotify':
        lyric_type, result = search_lyrics_by_spotify_url(track.track_url, track, lrc)
        if not lyric_type:
            source_type = 'genius'

    if source_type == "genius":
        result = search_lyrics_by_name_artist(track.track_name, track.track_artists)
        if result:
            lyric_type = 'txt'

    if result:
        # logging.warning(f"{track}|||{result}")
        return lyric_type, result
    return None, None


def extract_info_from_file(file):
    metadata = Tagger(file)

    url = get_valid_spotify_url(metadata.get('url', []))
    comment_type = 'WXXX'
    if not url:
        comment_type = 'source'
        url = get_valid_spotify_url(metadata.get('source', []))
    if not url:
        comment_type = 'XXX comment'
        url = get_valid_spotify_url(metadata.get('comment', []))
    if not url:
        comment_type = 'NULL comment'
        url = get_valid_spotify_url(metadata.get('commentNULL', []))
    if not url:
        comment_type = 'ENG comment'
        url = get_valid_spotify_url(metadata.get('commentENG', []))

    if not url:
        comment_type = " Invalid"

    logging.debug(f"Uses {comment_type} Url - {url}")



    artist = metadata.get('artist', [])
    title = metadata.get('title', [])
    album = metadata.get('album', [])
    track = Track(track_name=title[0] if title else '',
                  track_artists=artist[0] if artist else [],
                  track_url=url if url else '',
                  album_name=album[0] if album else '')
    # logging.info(f"{file}, {track}")
    return track


def get_valid_spotify_url(strings):
    spotify_track_url = "https://open.spotify.com/track/"
    if not strings:
        return None
    for string in strings:
        if string and spotify_track_url in "".join(string):
            track_id = "".join(string).replace(spotify_track_url, "")
            track_id = track_id.split("?")[0]  # Remove any trailing params
            return spotify_track_url + track_id

    return None