import logging
from difflib import SequenceMatcher
from pathlib import Path

from lyrics_searcher.auth import get_auth

from lyrics_searcher.utils import Track
from syrics.api import Spotify

from lyricsgenius.genius import Genius


def write_to_file(lyric_type: str, root: Path, filename: str, data: str):
    if lyric_type == 'lrc':
        ext = ".lrc"
    else:
        ext = ".txt"

    destination = root / (filename + ext)
    with open(destination, 'w', encoding="utf-8") as f:
        f.write(data)
        f.flush()


def _convert_to_lrc(data: dict):
    if not data:
        return None

    for line in data.get('lyrics', {}).get('lines', []):
        minutes = int(int(line.get('startTimeMs', '-1')) / (1000 * 60))
        seconds = int((int(line.get('startTimeMs', '-1')) / 1000) % 60)
        centiseconds = int((int(line.get('startTimeMs', '-1')) % 1000) / 10)

        line["TimeStamp"] = f"{minutes}:{seconds}:{centiseconds}"
        line.pop('startTimeMs')
        line.pop('syllables')
        line.pop('endTimeMs')
    return data.get('lyrics')


class LyricsSearcher:
    def __init__(self, sp_dc, g_tok):
        self.genius = Genius(g_tok)
        self.sp = Spotify(sp_dc)

        self.genius.verbose = False
        self.genius.skip_non_songs = True
        self.genius.timeout = 60
        self.genius.sleep_time = 2
        self.genius.retries = 7

    def get_spotify_lyrics(self, t_url=None, t_id=None, track_info=None, lrc: bool = False):

        if not any((t_url, t_id)):
            return None, None

        if t_url:
            lyrics = self._spot_via_url(t_url)
        elif t_id:
            lyrics = self._spot_via_url(t_id)
        else:
            return None, None

        #if lyrics:
         #   logging.warning(lyrics)
        if not lyrics:
            return None, None
        elif lyrics.get('syncType') == 'LINE_SYNCED' and lrc:
            return 'lrc', self.create_spotify_lrc(track_info, lyrics)
        elif lyrics.get('syncType') == 'UNSYNCED' or lyrics.get('syncType') == 'LINE_SYNCED' and not lrc:
            return 'txt', self.create_spotify_txt(lyrics)
        else:
            return None, None

    def create_spotify_lrc(self, track: Track, lines_array):
        out_str = ''
        if track:
            out_str += f"[ti:{track.track_name}]\n"
            out_str += f"[ar:{track.track_artists}]\n"
            out_str += f"[al:{track.album_name}]\n"
        out_str += f"[by:Drag(JCE) via lyric-finder]\n"

        out_str += "\n"

        for line in lines_array.get('lines'):
            out_str += f"[{line.get('TimeStamp')}] {line.get('words')}\n"

        return out_str

    def create_spotify_txt(self, lines):
        out_str = ''
        for line in lines.get('lines'):
            out_str += f"{line.get('words')}\n"

        return out_str

    def get_genius_lyrics(self, track):

        song = self.genius.search_song(track.track_name, track.track_artists[0])
        if not song:
            return None
        #logging.info(f"{track}|||{song}")
        title_match = SequenceMatcher(None, song.title.lower(), track.track_name.lower()).quick_ratio()
        if title_match > 0.75:
            return song.lyrics
        else:
            return None

    def _spot_via_id(self, t_id: str):
        lyrics = _convert_to_lrc(self.sp.get_lyrics(t_id))
        return lyrics

    def _spot_via_url(self, url: str):
        t_id = url.replace('https://open.spotify.com/track/', '').replace('/', '')
        lyrics = _convert_to_lrc(self.sp.get_lyrics(t_id))
        return lyrics


if __name__ == "__main__":
    # test()

    spdc = get_auth("spotify")
    g_tok = get_auth("genius")
    lyrics_searcher = LyricsSearcher(spdc, g_tok)

    has_no_lyrics = 'https://open.spotify.com/track/0TYMrEy482BCnbvDxiSW1T'
    has_timed_lyrics = 'https://open.spotify.com/track/0YjFF1QQ3L3dNMkXHjEXFy?si=84feb6de68544751'
    has_no_time_lrc = 'https://open.spotify.com/track/5QEE5q4DCa7LhJz19lXF8M?si=e7b7c142e4e949ec'

    sunfish = Track(track_name='Mr. Sunfish', track_artists=['YonKaGor'], album_name='Mr. Sunfish')
    consideration = Track(track_name='Consideration', track_artists=['Rihanna'])

    lyric_type, lyrics = lyrics_searcher.get_spotify_lyrics(t_url=has_no_time_lrc, track_info=sunfish)
    print(lyrics)

    genius_lyrics = lyrics_searcher.get_genius_lyrics(consideration)
    print(genius_lyrics)
