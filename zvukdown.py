#!/usr/bin/env python3
import glob
import threading
import os
import requests
import sys
import time
import json
import logging
import pickle
from pathlib import Path
from shutil import copyfile
from typing import Any
from http.cookiejar import MozillaCookieJar
import platform

from mutagen.flac import FLAC, Picture

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

HELP_MESSAGE = """
Пример использования:
  python zvuk_downloader.py --threads=10 https://zvuk.com/artist/852542
  python zvuk_downloader.py https://zvuk.com/artist/852542
  python zvuk_downloader.py https://zvuk.com/release/29015282
  python zvuk_downloader.py https://zvuk.com/playlist/8545187
  python zvuk_downloader.py https://zvuk.com/track/12776890
  python zvuk_downloader.py https://zvuk.com/selection/1
  python zvuk_downloader.py https://zvuk.com/podcast/14574115
  python zvuk_downloader.py https://zvuk.com/abook/24072774
  python zvuk_downloader.py --check-auth

Дополнительные параметры:
  --output-path=DIR   Указать папку для загрузки
  --format=1|2|3       Формат аудио: 1=MP3-128, 2=MP3-320, 3=FLAC (по умолчанию)

Требуется файл cookies.txt в формате Netscape:
  - Получить можно с помощью расширений браузера:
    • Chrome: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
    • Firefox: https://addons.mozilla.org/en-US/firefox/addon/export-cookies-txt/
  - Убедитесь, что файл содержит cookies для домена zvuk.com
  - Токен будет автоматически извлечён из cookies (auth)
  - Аккаунт должен иметь активную подписку (Prime)

Настройки:
  album_folder_template: Путь сохранения релизов. Поддерживаются шаблоны:
    {{.albumArtist}}, {{.releaseYear}}, {{.albumTitle}}
    Примеры:
      Unix:      "Artists/{{.albumArtist}}/{{.releaseYear}} - {{.albumTitle}}"
      Windows:   "Music\\{{.albumArtist}}\\{{.releaseYear}} - {{.albumTitle}}"
      Flat:      "{{.releaseYear}} - {{.albumArtist}} - {{.albumTitle}}"
"""

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

CACHE_FILE = "api_cache.pkl"
ALBUM_TEMPLATE = "Artists/{artist}/{year} - {title}" if platform.system() != "Windows" else "Music\\{artist}\\{year} - {title}"
OUTPUT_DIR = "zvuk_downloads"
FORMAT = "flac"

class zvukdown_:
    def __init__(self, max_threads=5):
        self.verify = True
        self.headers = {}
        self.cookies = None
        self.max_threads = max_threads
        self.cache = self.load_cache()

    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        return {}

    def save_cache(self):
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(self.cache, f)

    def cached_get(self, url, **kwargs):
        if url in self.cache:
            logging.info(f"Кэширован: {url}")
            return self.cache[url]
        for attempt in range(3):
            try:
                resp = requests.get(url, **kwargs)
                resp.raise_for_status()
                self.cache[url] = resp
                self.save_cache()
                return resp
            except requests.RequestException as e:
                logging.warning(f"Ошибка запроса ({attempt+1}/3): {e}")
                time.sleep(2)
        raise Exception(f"Не удалось получить {url}")

    def load_cookies(self):
        if os.path.exists("cookies.txt"):
            self.cookies = MozillaCookieJar()
            self.cookies.load("cookies.txt", ignore_discard=True, ignore_expires=True)

    def read_auth(self):
        self.load_cookies()
        if not self.cookies:
            raise Exception("Файл cookies.txt не найден или не содержит cookies.")

        token = None
        for cookie in self.cookies:
            if cookie.name == "access_token":
                token = cookie.value
                #token = "0688e3b7a8dd47f680009eddb565b87a"
                break

        if not token or len(token) != 32:
            raise Exception("Не удалось извлечь токен из cookies (auth). Возможно, cookies устарели.")

        self.headers = {
            "x-auth-token": token,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
            "Accept": "application/json",
            "Origin": "https://zvuk.com",
            "Referer": "https://zvuk.com/"
        }

        resp = self.cached_get("https://zvuk.com/api/v2/tiny/profile", headers=self.headers, cookies=self.cookies, verify=self.verify)
        data = resp.json()
        if data.get("result", {}).get("is_prime", False):
            raise Exception("Аккаунт не имеет активной подписки (is_prime = false).")
        logging.info("Токен действителен. Подписка активна.")

    def format_output_path(self, artist, year, title):
        path = ALBUM_TEMPLATE.format(artist=self.__ntfs(artist), year=year, title=self.__ntfs(title))
        return os.path.join(OUTPUT_DIR, path)

    def run_threads(self, items, target_fn, max_threads=None, show_progress=True):
        if max_threads is None:
            max_threads = self.max_threads
        from threading import Semaphore, Thread

        semaphore = Semaphore(max_threads)
        threads = []
        iterator = tqdm(items) if HAS_TQDM and show_progress else items

        for args in iterator:
            semaphore.acquire()
            def wrapped(*args):
                try:
                    target_fn(*args)
                finally:
                    semaphore.release()
            t = Thread(target=wrapped, args=(args,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    def __ntfs(self, filename):
        for ch in ['<', '>', '@', '%', '!', '+', ':', '"', '/', '\\', '|', '?', '*']:
            filename = filename.replace(ch, '_')
        filename = " ".join(filename.split())
        return filename.strip()

# ... остальные методы без изменений (вставляются ниже)

    def download_selection(self, selection_id):
        logging.info(f"Скачивание подборки: {selection_id}")
        url = f"https://zvuk.com/api/tiny/selection?id={selection_id}&include=track"
        r = self.cached_get(url, headers=self.headers, cookies=self.cookies, verify=self.verify)
        data = r.json()['result']['selection']
        title = data['title']
        track_ids = data['track_ids']
        out_dir = os.path.join('_selections', title)
        os.makedirs(out_dir, exist_ok=True)
        self.download_tracks(track_ids, out_dir)

    def download_podcast(self, podcast_id):
        logging.info(f"Скачивание подкаста: {podcast_id}")
        url = f"https://zvuk.com/api/tiny/podcasts?ids={podcast_id}"
        r = self.cached_get(url, headers=self.headers, cookies=self.cookies, verify=self.verify)
        data = r.json()['result']['podcasts'][str(podcast_id)]

        episodes = data.get('episodes', [])
        episode_ids = [episode['id'] for episode in episodes]

        def download_episode(episode_id):
            episode_url = f"https://zvuk.com/api/tiny/podcast_episodes?id={episode_id}"
            r = self.cached_get(episode_url, headers=self.headers, cookies=self.cookies, verify=self.verify)
            episode_data = r.json()['result']['episodes'][str(episode_id)]

            title = self.__ntfs(episode_data['title'])
            author = self.__ntfs(episode_data['author'])
            filename = f"{title}.mp3"
            filepath = os.path.join("_podcasts", title)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            stream_url = episode_data['stream_url']
            with open(filepath, 'wb') as f:
                f.write(requests.get(stream_url, verify=self.verify).content)

            logging.info(f"Скачано: {filename}")

        self.run_threads(episode_ids, download_episode)

    def download_audiobook(self, audiobook_id):
        logging.info(f"Скачивание аудиокниги: {audiobook_id}")
        url = f"https://zvuk.com/api/tiny/audiobooks?ids={audiobook_id}"
        r = self.cached_get(url, headers=self.headers, cookies=self.cookies, verify=self.verify)
        data = r.json()['result']['audiobooks'][str(audiobook_id)]

        chapters = data.get('chapters', [])
        chapter_ids = [chapter['id'] for chapter in chapters]

        def download_chapter(chapter_id):
            chapter_url = f"https://zvuk.com/api/tiny/audiobook_chapters?id={chapter_id}"
            r = self.cached_get(chapter_url, headers=self.headers, cookies=self.cookies, verify=self.verify)
            chapter_data = r.json()['result']['chapters'][str(chapter_id)]

            title = self.__ntfs(chapter_data['title'])
            author = self.__ntfs(chapter_data['author'])
            filename = f"{title}.mp3"
            filepath = os.path.join("_audiobooks", title)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            stream_url = chapter_data['stream_url']
            with open(filepath, 'wb') as f:
                f.write(requests.get(stream_url, verify=self.verify).content)

            logging.info(f"Скачано: {filename}")

        self.run_threads(chapter_ids, download_chapter)

    def download_track(self, track_id):
        print(f"Скачивание трека: {track_id}")
        track_url = f"https://zvuk.com/api/tiny/tracks?ids={track_id}"
        r = requests.get(track_url, headers=self.headers, verify=self.verify)
        r.raise_for_status()
        track = r.json()['result']['tracks'][str(track_id)]

        #print(json.dumps(track, indent=2))

        title = self.__ntfs(track['title'])
        performer = self.__ntfs(track['credits'])
        album = self.__ntfs(track['release_title'])
        out_dir = os.path.join('_tracks', f"{performer} - {album}")
        os.makedirs(out_dir, exist_ok=True)
        filename = f"{track['position']:02d} - {title}.flac"
        filepath = os.path.join(out_dir, filename)

        stream_url = requests.get(
            "https://zvuk.com/api/tiny/track/stream",
            params={"id": track_id, "quality": "flac"},
            headers=self.headers,
            verify=self.verify
        ).json()['result']['stream']

        with open(filepath, 'wb') as f:
            f.write(requests.get(stream_url, verify=self.verify).content)

        audio = FLAC(filepath)
        audio['artist'] = performer
        audio['title'] = title
        audio['album'] = album
        audio['tracknumber'] = str(track['position'])
        audio['date'] = str(track.get('release_date', '')[:4])
        audio.save()

        print(f"Скачано: {filepath}")

    def download_release(self, release_id):
        print(f"Скачивание релиза: {release_id}")
        url = f"https://zvuk.com/api/tiny/releases?ids={release_id}"
        r = requests.get(url, headers=self.headers, verify=self.verify)
        r.raise_for_status()
        release = r.json()['result']['releases'][str(release_id)]
        artist = self.__ntfs(release['credits'])
        year = str(release['date'])[:4]
        album = self.__ntfs(release['title'])
        out_dir = os.path.join('_releases', artist, f"{year} - {album}")
        os.makedirs(out_dir, exist_ok=True)
        self.download_tracks(release['track_ids'], out_dir)

    def download_playlist(self, playlist_id):
        print(f"Скачивание плейлиста: {playlist_id}")
        url = f"https://zvuk.com/api/tiny/playlists?ids={playlist_id}&include=track,release"
        r = requests.get(url, headers=self.headers, verify=self.verify)
        r.raise_for_status()
        data = r.json()['result']['playlists'][str(playlist_id)]
        title = self.__ntfs(data['title'])
        out_dir = os.path.join('_playlists', title)
        os.makedirs(out_dir, exist_ok=True)
        self.download_tracks(data['track_ids'], out_dir)

    def download_artist(self, artist_id):
        print(f"Скачивание всего у артиста: {artist_id}")
        url = f"https://zvuk.com/api/tiny/artists/releases?artist_id={artist_id}"
        r = requests.get(url, headers=self.headers, verify=self.verify)
        r.raise_for_status()
        data = r.json()['result']
        self.run_threads([(rel['id'],) for rel in data], lambda r: self.download_release(r[0]))

    def download_tracks(self, track_ids, out_dir):
        url = "https://zvuk.com/api/tiny/tracks?ids=" + ','.join(map(str, track_ids))
        r = requests.get(url, headers=self.headers, verify=self.verify)
        r.raise_for_status()
        tracks = r.json()['result']['tracks']

        def download_single(track_id, track):
            print(json.dumps(track, indent=2))
            title = self.__ntfs(track['title'])
            performer = self.__ntfs(track['credits'])
            filename = f"{track['position']:02d} - {title}.flac"
            filepath = os.path.join(out_dir, filename)

            stream_url = requests.get(
                "https://zvuk.com/api/tiny/track/stream",
                params={"id": track_id, "quality": "flac"},
                headers=self.headers,
                verify=self.verify
            ).json()['result']['stream']

            with open(filepath, 'wb') as f:
                f.write(requests.get(stream_url, verify=self.verify).content)
            audio = FLAC(filepath)
            audio['artist'] = performer
            audio['title'] = title
            audio['album'] = track['release_title']
            audio['tracknumber'] = str(track['position'])
            audio['date'] = str(track.get('release_date', '')[:4])
            audio.save()
            print(f"Скачано: {filepath}")

        self.run_threads(list(tracks.items()), lambda item: download_single(*item))

    def download_all(self, links):
        parsed_links = []
        for link in links:
            if "/track/" in link:
                track_id = link.split("/track/")[-1].split("/")[0]
                parsed_links.append(("track", track_id))
            elif "/selection/" in link:
                selection_id = link.split("/selection/")[-1].split("/")[0]
                parsed_links.append(("selection", selection_id))
            elif "/release/" in link:
                release_id = link.split("/release/")[-1].split("/")[0]
                parsed_links.append(("release", release_id))
            elif "/playlist/" in link:
                playlist_id = link.split("/playlist/")[-1].split("/")[0]
                parsed_links.append(("playlist", playlist_id))
            elif "/artist/" in link:
                artist_id = link.split("/artist/")[-1].split("/")[0]
                parsed_links.append(("artist", artist_id))
            elif "/podcast/" in link:  # Новый блок для подкастов
                podcast_id = link.split("/podcast/")[-1].split("/")[0]
                parsed_links.append(("podcast", podcast_id))
            elif "/abook/" in link:  # Новый блок для аудиокниг
                abook_id = link.split("/abook/")[-1].split("/")[0]
                parsed_links.append(("abook", abook_id))
            else:
                print(f"Неизвестный формат ссылки: {link}")

        def dispatch(link_type, value):
            if link_type == "track":
                self.download_track(value)
            elif link_type == "selection":
                self.download_selection(value)
            elif link_type == "podcast":  # Новое условие для подкастов
                self.download_podcast(value)
            elif link_type == "abook":  # Новое условие для аудиокниг
                self.download_audiobook(value)
            elif link_type == "release":
                self.download_release(value)
            elif link_type == "playlist":
                self.download_playlist(value)
            elif link_type == "artist":
                self.download_artist(value)

        self.run_threads(parsed_links, lambda t: dispatch(*t))

    def check_dependencies():
        missing = []
        try:
            import mutagen
        except ImportError:
            missing.append('mutagen')
        try:
            import tqdm
        except ImportError:
            print("(опционально) tqdm не найден. Установите для прогресс-бара: pip install tqdm")
        if missing:
            print("Обязательные зависимости не найдены:", ', '.join(missing))
            print("Установите их с помощью:")
            print(f"  pip install {' '.join(missing)}")
            sys.exit(1)



if __name__ == '__main__':
    if '--help' in sys.argv or '-h' in sys.argv or len(sys.argv) == 1:
        print(HELP_MESSAGE)
        sys.exit(0)

    if '--check-auth' in sys.argv:
        z = zvukdown_()
        try:
            z.read_auth()
            print("[OK] Аутентификация прошла успешно. Подписка активна.")
        except Exception as e:
            print(f"[ERROR] {e}")
        sys.exit(0)

    max_threads = 5
    urls = []
    for arg in sys.argv[1:]:
        if arg.startswith('--threads='):
            try:
                max_threads = int(arg.split('=')[1])
            except ValueError:
                print("Неверное значение для --threads. Должно быть целое число.")
                sys.exit(1)
        elif arg.startswith('--output-path='):
            OUTPUT_DIR = arg.split('=', 1)[1]
        elif arg.startswith('--format='):
            fmt = arg.split('=', 1)[1]
            if fmt == '1': FORMAT = 'mp3-128'
            elif fmt == '2': FORMAT = 'mp3-320'
            elif fmt == '3': FORMAT = 'flac'
            else:
                print("Неверное значение для --format. Допустимы: 1, 2, 3")
                sys.exit(1)
        else:
            urls.append(arg)

    z = zvukdown_(max_threads=max_threads)
    z.read_auth()
    z.download_all(urls)
