```markdown
# Zvuk Downloader

## Скачиватель музыкальных композиций и медиафайлов со Zvuk.com

### Требования для работы:
- Наличие активного аккаунта с подпиской Prime или пробным периодом на платформе Zvuk.com.
- Валидный файл куков (`cookies.txt`) в формате Netscape, содержащий актуальный токен авторизации (`auth`).

### Как получить токен авторизации:
1. Войдите в аккаунт на сайте Zvuk.com.
2. Используйте расширение для браузера, чтобы экспортировать куки:
   - **Chrome**: [Get Cookies.txt](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - **Firefox**: [Export Cookies to Text File](https://addons.mozilla.org/en-US/firefox/addon/export-cookies-txt/)
3. Убедитесь, что файл содержит токен авторизации для домена `zvuk.com`.

### Примеры использования:
'''
python zvuk_downloader.py --threads=10 https://zvuk.com/artist/852542
'''
'''
python zvuk_downloader.py https://zvuk.com/release/29015282
'''
'''
python zvuk_downloader.py https://zvuk.com/playlist/8545187
'''
'''
python zvuk_downloader.py https://zvuk.com/track/12776890
'''
'''
python zvuk_downloader.py https://zvuk.com/selection/1
'''
'''
python zvuk_downloader.py https://zvuk.com/podcast/14574115
'''
'''
python zvuk_downloader.py https://zvuk.com/abook/24072774
'''
'''
python zvuk_downloader.py --check-auth
'''
### Доступные параметры:
- `--threads=N`: Устанавливает количество параллельных потоков скачивания (по умолчанию 5).
- `--output-path=DIR`: Определяет директорию для сохранения файлов.
- `--format=1|2|3`: Выбор качества аудио (1=MP3-128, 2=MP3-320, 3=FLAC; по умолчанию FLAC).

### Шаблон путей:
Пути для сохранения поддерживают переменные-шаблоны:
- `{ {.albumArtist} }`: Имя исполнителя.
- `{ {.releaseYear} }`: Год издания.
- `{ {.albumTitle} }`: Название альбома.

Примеры:
- **Unix**: `"Artists/{ {.albumArtist} }/{ {.releaseYear} } - { {.albumTitle} }"`
- **Windows**: `"Music\\{ {.albumArtist} }\\{ {.releaseYear} } - { {.albumTitle} }"`
- **Flat**: `"{ {.releaseYear} } - { {.albumArtist} } - { {.albumTitle} }"`
