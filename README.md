# YouTube Downloader
Description
This is a simple graphical user interface (GUI) application for downloading YouTube videos and playlists. It uses yt_dlp for downloading content, DearPyGui for the UI, and optionally FFmpeg for merging video and audio streams. The application supports selecting video quality, output format (MP4, MKV, WEBM), and displays thumbnails, progress, and status updates. It also includes light/dark theme switching and handles playlists with user confirmation.
The code is designed to be bundled into a standalone executable using PyInstaller, with FFmpeg included for Windows users.
Features

Download single videos or entire playlists from YouTube.
Preview video thumbnail and metadata (title, duration, channel).
Select video quality (e.g., 1080p, 720p) with or without audio.
Choose output format: MP4, MKV, or WEBM.
Automatic merging of video and audio using FFmpeg (if installed or bundled).
Progress bar and status messages during downloads.
Light and dark theme toggle.
Asynchronous thumbnail loading and info fetching to keep the UI responsive.
Error handling for missing dependencies like FFmpeg or libraries.
Support for Cyrillic characters and emojis via font loading.

# Requirements

Python 3.8+
yt_dlp: For downloading YouTube content.
dearpygui: For the GUI.
Optional: Pillow and requests for thumbnail loading.
Optional but recommended: FFmpeg for merging video/audio streams (automatically bundled in PyInstaller builds).

# Installation

Clone or download the repository.
Install dependencies:textpip install yt-dlp dearpygui pillow requests
(Optional) Install FFmpeg:
Download from ffmpeg.org and add to your PATH.
For Windows PyInstaller builds, FFmpeg is bundled in the bin directory.

Run the script:textpython main.py

To build a standalone executable (Windows):

Install PyInstaller: pip install pyinstaller
Run: pyinstaller --add-data "bin;bin" --onefile main.py (assuming bin contains ffmpeg.exe).

# Usage

Launch the application.
Enter a YouTube video or playlist URL in the "Ссылка на видео или плейлист" field.
Select a save folder using the "Обзор..." button (defaults to Downloads).
Click "Загрузить" to fetch video info.
If it's a playlist, confirm whether to download the entire playlist.
In the format selection dialog:
Choose quality from the radio buttons.
Select output format (MP4, MKV, WEBM).
Click "Загрузить" to start the download.

Monitor progress in the main window.
Toggle themes with the "Светлая тема" / "Тёмная тема" button.

# Troubleshooting

FFmpeg not found: Install FFmpeg and add it to PATH. The app will fall back to single-format downloads without merging.
Thumbnail not loading: Ensure Pillow and requests are installed.
Errors with yt_dlp: Update with pip install --upgrade yt-dlp.
GUI issues: Ensure DearPyGui is up to date.
Playlist downloads: Files are named with playlist index for ordering.

# License
This project is open-source and available under the MIT License.

# Загрузчик YouTube
# Описание
Это простое графическое приложение (GUI) для скачивания видео и плейлистов с YouTube. Оно использует yt_dlp для загрузки контента, DearPyGui для интерфейса и опционально FFmpeg для слияния видео и аудио потоков. Приложение поддерживает выбор качества видео, формата вывода (MP4, MKV, WEBM), отображение миниатюр, прогресса и обновлений статуса. Также включено переключение светлой/тёмной темы и обработка плейлистов с подтверждением пользователя.
Код предназначен для сборки в standalone-исполняемый файл с помощью PyInstaller, с включением FFmpeg для пользователей Windows.
Возможности

# Скачивание отдельных видео или целых плейлистов с YouTube.
Предпросмотр миниатюры видео и метаданных (название, длительность, канал).
Выбор качества видео (например, 1080p, 720p) с аудио или без.
Выбор формата вывода: MP4, MKV или WEBM.
Автоматическое слияние видео и аудио с помощью FFmpeg (если установлен или включён в сборку).
Полоса прогресса и сообщения статуса во время загрузки.
Переключение светлой и тёмной темы.
Асинхронная загрузка миниатюр и информации для отзывчивости интерфейса.
Обработка ошибок для отсутствующих зависимостей, таких как FFmpeg или библиотеки.
Поддержка кириллицы и эмодзи через загрузку шрифтов.

# Требования

Python 3.8+
yt_dlp: Для скачивания контента с YouTube.
dearpygui: Для GUI.
Опционально: Pillow и requests для загрузки миниатюр.
Опционально, но рекомендуется: FFmpeg для слияния видео/аудио потоков (автоматически включается в сборках PyInstaller).

# Установка

Клонируйте или скачайте репозиторий.
Установите зависимости:textpip install yt-dlp dearpygui pillow requests
(Опционально) Установите FFmpeg:
Скачайте с ffmpeg.org и добавьте в PATH.
Для сборок PyInstaller на Windows FFmpeg включается в директорию bin.

Запустите скрипт:textpython main.py

Для сборки standalone-исполняемого файла (Windows):

Установите PyInstaller: pip install pyinstaller
Запустите: pyinstaller --add-data "bin;bin" --onefile main.py (предполагая, что bin содержит ffmpeg.exe).

# Использование

Запустите приложение.
Введите URL видео или плейлиста с YouTube в поле "Ссылка на видео или плейлист".
Выберите папку сохранения с помощью кнопки "Обзор..." (по умолчанию — Downloads).
Нажмите "Загрузить" для получения информации о видео.
Если это плейлист, подтвердите скачивание всего плейлиста.
В диалоге выбора формата:
Выберите качество из радиокнопок.
Выберите формат вывода (MP4, MKV, WEBM).
Нажмите "Загрузить" для начала скачивания.

Следите за прогрессом в главном окне.
Переключайте темы кнопкой "Светлая тема" / "Тёмная тема".

# Устранение неисправностей

FFmpeg не найден: Установите FFmpeg и добавьте в PATH. Приложение вернётся к скачиванию в одном формате без слияния.
Миниатюра не загружается: Убедитесь, что установлены Pillow и requests.
Ошибки с yt_dlp: Обновите с помощью pip install --upgrade yt-dlp.
Проблемы с GUI: Убедитесь, что DearPyGui обновлён.
Скачивание плейлистов: Файлы именуются с индексом плейлиста для порядка.

Лицензия
Этот проект является открытым и доступен под лицензией MIT.
