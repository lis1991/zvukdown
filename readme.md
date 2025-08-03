# Zvuk Downloader — Скачивание музыки с Zvuk.com

**Zvuk Downloader** — инструмент для скачивания аудиоконтента с платформы Zvuk.com. Программа позволяет сохранять треки, альбомы, плейлисты и другой медиаконтент.

**📋 Примеры использования**

``` python zvuk_downloader.py --threads=10 https://zvuk.com/artist/852542```

``` python zvuk_downloader.py https://zvuk.com/release/29015282```

``` python zvuk_downloader.py https://zvuk.com/playlist/8545187```

``` python zvuk_downloader.py https://zvuk.com/track/12776890```

``` python zvuk_downloader.py https://zvuk.com/selection/1```

``` python zvuk_downloader.py https://zvuk.com/podcast/14574115```

``` python zvuk_downloader.py https://zvuk.com/abook/24072774```

``` python zvuk_downloader.py --check-auth```

**⚙️ Параметры командной строки**

> `–threads=N` — настройка количества параллельных потоков (по умолчанию: 5)

> `–output-path=DIR` — путь для сохранения файлов

> `–format=X` — выбор формата аудио:

> 1 — MP3 128 kbps

> 2 — MP3 320 kbps

> 3 — FLAC (по умолчанию)

**🔍 Основные требования**

> Аккаунт с активной подпиской Prime

> Файл cookies.txt в формате Netscape

> Токен авторизации (автоматически извлекается из cookies)

**📁 Структура сохранения файлов**

> Программа поддерживает шаблоны именования:

> `Unix-система: Artists/{{.albumArtist}}/{{.releaseYear}} - {{.albumTitle}}`

> `Windows: Music\{{.albumArtist}}\{{.releaseYear}} - {{.albumTitle}}`

> `Плоская структура: {{.releaseYear}} - {{.albumArtist}} - {{.albumTitle}}`

**🔑 Получение cookies**

> Для Chrome: [**Get cookies.txt LOCALLY**](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)

> Для Firefox: [**Export Cookies**](https://addons.mozilla.org/en-US/firefox/addon/export-cookies-txt/)

**🔄 Проверка авторизации**

> Для проверки работоспособности авторизации используйте:

```
python zvuk_downloader.py --check-auth
```

**🗑️ Очистка кэша**

> При возникновении проблем с авторизацией выполните:

```
rm -rf api_cache.pkl
```

**⚠️ Важные примечания**

> Убедитесь, что файл cookies содержит актуальные данные для домена

> Проверьте наличие активной подписки Prime

> Файл cookies должен содержать действующий токен авторизации (auth)

> Для корректной работы требуется Python 3 и установленные зависимости

**🛠️ Дополнительная информация**

> Помощь и поддержка
> Для получения дополнительной информации используйте команду:

```
python zvuk_downloader.py --help
```

> **Лицензирование**
> Программа распространяется под лицензией MIT. Все права защищены.



