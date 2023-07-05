import argparse
import concurrent.futures
import json
import logging
import multiprocessing
import queue
import sys
import threading
from pathlib import Path
from queue import Queue

import lyrics_searcher.api as api
from lyrics_searcher import CONFIG_DIR
from lyrics_searcher.auth import save_auth, create_auth, get_auth

logging.basicConfig(level=logging.INFO)
SUPPORTED_FILETYPES = [".mp3", ".wav", ".flac", ".ogg", ".wma", ".m4a", ".oga"]
end_of_search = threading.Event()
locks = {}


def search_lyrics_single(args):
    if args.method == 'artist':
        result = api.search_lyrics_by_name_artist(args.track_name, args.track_artist)
    elif args.method == 'spotify_url':
        _, result = api.search_lyrics_by_spotify_url(args.spotify_url, lrc=args.lrc)
    elif args.method == 'spotify_id':
        _, result = api.search_lyrics_by_spotify_track_id(args.spotify_track_id, lrc=args.lrc)
    elif args.method == 'file':
        _, result = api.search_lyrics_by_file(Path(args.file), lrc=args.lrc)
    else:
        logging.exception(f"Invalid search method: {args.method}")
        return

    if result:
        print(result)
    else:
        print("No Lyrics Found", file=sys.stderr)


def search_files(search_path: Path, file_queue: Queue):
    for filetype in SUPPORTED_FILETYPES:
        music_files = search_path.rglob(f"*{filetype}")
        for music_file in music_files:
            file_queue.put(music_file)
    logging.info("Finished Scanning")
    end_of_search.set()


def process_file_queue(file_queue: Queue[Path], lrc: bool = True):
    while True:
        try:
            music_file = file_queue.get(timeout=5)
            process_music_file(music_file, lrc)
        except queue.Empty:
            if end_of_search.is_set():
                file_queue.task_done()
                logging.info("Empty -Exp Thread Done")
                break
        except Exception as e:
            logging.error("Exception", e)
        finally:
            file_queue.task_done()


def process_music_file(music_file: Path, lrc: bool):
    lyric_type, result = api.search_lyrics_by_file(music_file, lrc)
    if not result:
        logging.info(f"No lyrics found for: {music_file}")
        return

    lyric_file = music_file.parent
    filename = music_file.stem
    destination = lyric_file / (filename + '.' + lyric_type)

    if not locks.get(str(destination)):
        locks[str(destination)] = threading.Lock()

    with locks[str(destination)]:
        if not should_update(lyric_file, filename, result):
            return

        with open(destination, 'w', encoding="utf-8") as f:
            f.write(result)
            logging.info(f"Lyrics file created: {destination}")


def should_update(lyric_file: Path, filename: str, result: str) -> bool:
    txt = lyric_file / (filename + ".txt")
    lrc = lyric_file / (filename + ".lrc")

    existing = (txt, lrc)
    update = False

    for file in existing:
        if file.exists():
            with open(file, encoding="utf-8") as f:
                if not result == f.read():
                    logging.info(f"Deleting {file}")
                    update = True
                    if not locks.get(str(file)):
                        locks[str(file)] = threading.Lock()

                    with locks[str(file)]:
                        file.unlink()
                else:
                    logging.info(f"{file} is current")
                    return False

    return update


def search_lyrics_batch(args):
    search_path = Path(args.search_path)

    if not search_path.is_dir():
        logging.exception(f"Invalid search path: {search_path}")
        return

    music_files_queue = Queue()

    file_search_thread = threading.Thread(target=search_files, args=(search_path, music_files_queue))
    file_search_thread.start()

    num_threads = min(6, multiprocessing.cpu_count() // 2)  # Number of threads in the thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Start worker threads to process the file queue
        for _ in range(num_threads):
            executor.submit(process_file_queue, music_files_queue, not args.txt)

    # Wait for the file search thread to finish
    file_search_thread.join()

    # Wait for all files to be processed
    music_files_queue.join()


def do_auth_mode(args):
    CONFIG_DIR.mkdir(exist_ok=True)
    auth_path = CONFIG_DIR / "auth.json"
    if not auth_path.exists():
        create_auth()

    if args.auth_command == 'set':
        service = args.service
        token = args.token
        logging.info(f"Saving {service} token")
        save_auth(service, token)
    elif args.auth_command == 'get':
        service = args.service
        token = get_auth(service)
        if token:
            print(token)
        else:
            print("No saved token, run auth set")
    else:
        logging.exception(f"Invalid Auth Command: {args.auth_command}")





def parse_args():
    parser = argparse.ArgumentParser(description='Lyrics Search CLI')
    parser.add_argument("-y", "--lrc", help="Get output in lrc format if available", action="store_true")
    parser.add_argument("-t", "--txt", help="Get files in txt format in batch mode", action="store_true")
    subparsers = parser.add_subparsers(dest='mode', help='Mode')

    # Single mode subcommand
    single_parser = subparsers.add_parser('single', help='Single mode')
    single_subparsers = single_parser.add_subparsers(dest='method', help='Search method')

    # Name/artist subcommand
    name_artist_parser = single_subparsers.add_parser('artist', help='Search lyrics by track name and artist')
    name_artist_parser.add_argument('track_name', type=str, help='Track name')
    name_artist_parser.add_argument('track_artist', type=str, help='Track artist')

    # Spotify URL subcommand
    spotify_url_parser = single_subparsers.add_parser('spotify_url', help='Search lyrics by Spotify URL')
    spotify_url_parser.add_argument('spotify_url', type=str, help='Spotify URL')

    # Spotify track ID subcommand
    spotify_track_id_parser = single_subparsers.add_parser('spotify_id', help='Search lyrics by Spotify track ID')
    spotify_track_id_parser.add_argument('spotify_track_id', type=str, help='Spotify track ID')

    file_parser = single_subparsers.add_parser('file', help='Search lyrics by the path to an audio file')
    file_parser.add_argument('file', type=str, help='Path to file')

    # Batch mode subcommand
    batch_parser = subparsers.add_parser('batch', help='Batch mode')
    batch_parser.add_argument('search_path', type=str, help='Search path')

    # Auth Mode Subcommand
    auth_parser = subparsers.add_parser('auth', help="Commands with keys/tokens")
    direction_parser = auth_parser.add_subparsers(dest='auth_command')

    # set subcommand
    set_parser = direction_parser.add_parser('set')
    set_parser.add_argument('service', choices=['spotify', 'genius'], help='Specify the service')
    set_parser.add_argument('token', help='Specify the token value')

    # gte subcommand
    get_parser = direction_parser.add_parser('get')
    get_parser.add_argument('service', choices=['spotify', 'genius'], help='Specify the service')

    return parser.parse_args()


def main():
    args = parse_args()

    if args.mode == 'single':
        search_lyrics_single(args)
    elif args.mode == 'batch':
        search_lyrics_batch(args)
    elif args.mode == 'auth':
        do_auth_mode(args)
    else:
        logging.exception(f"Invalid mode: {args.mode}")


if __name__ == '__main__':
    main()
