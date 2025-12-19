import sys
import os

if getattr(sys, 'frozen', False):
    # Если запущено как .exe (PyInstaller)
    meipass = sys._MEIPASS
    bin_path = os.path.join(meipass, 'bin')
    os.environ['PATH'] = bin_path + os.pathsep + os.environ.get('PATH', '')


from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QProgressBar, QFileDialog, QComboBox,
                               QGroupBox, QCheckBox, QMessageBox, QDialog,
                               QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from urllib.parse import urlparse, parse_qs
import subprocess
import shutil

try:
    import yt_dlp
except ImportError:
    print("yt-dlp library is not installed.")
    print("Install it with: pip install --upgrade yt-dlp")
    sys.exit(1)


class VideoInfoThread(QThread):
    """
    Thread to fetch video/playlist info without blocking the UI
    """
    info_ready = Signal(dict)  # video information dictionary
    error = Signal(str)        # error message

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

                # If playlist, take first valid dict entry
                if info.get('_type') == 'playlist' and info.get('entries'):
                    dict_entries = [e for e in info['entries'] if isinstance(e, dict)]
                    if dict_entries:
                        info = dict_entries[0]

                processed_formats = []

                def collect_formats(entry):
                    video_formats = {}
                    audio_formats = []
                    for f in entry.get('formats', []):
                        format_id = f.get('format_id', 'N/A')
                        height = f.get('height')
                        vcodec = f.get('vcodec', 'none')
                        acodec = f.get('acodec', 'none')
                        ext = f.get('ext', 'unknown')
                        fps = f.get('fps', 0)

                        if height and vcodec != 'none':
                            quality_key = f"{height}p"
                            if fps and fps > 30:
                                quality_key += f" {fps}fps"
                            if quality_key not in video_formats:
                                video_formats[quality_key] = {
                                    'format_id': format_id,
                                    'height': height,
                                    'ext': ext,
                                    'has_audio': acodec != 'none'
                                }

                        if acodec != 'none' and vcodec == 'none':
                            audio_formats.append(format_id)

                    sorted_formats = sorted(video_formats.items(), key=lambda x: x[1]['height'] or 0, reverse=True)
                    out = []
                    for quality, data in sorted_formats:
                        out.append({
                            'quality': quality,
                            'format_id': data['format_id'],
                            'ext': data['ext'],
                            'has_audio': data['has_audio']
                        })
                    return out

                processed_formats = collect_formats(info)
                info['processed_formats'] = processed_formats
                self.info_ready.emit(info)

        except Exception as e:
            self.error.emit(f"Error fetching video info: {str(e)}")



class FormatSelectionDialog(QDialog):
    """
    Dialog window to select video quality and output format
    """
    def __init__(self, video_info, thumbnail_pixmap, parent=None):
        super().__init__(parent)
        self.video_info = video_info
        self.selected_format = None
        self.selected_file_format = 'mp4'
        self.init_ui(thumbnail_pixmap)

    def init_ui(self, thumbnail_pixmap):
        self.setWindowTitle("Select Quality and Format")
        self.setMinimumSize(600, 700)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Thumbnail
        thumbnail_label = QLabel()
        if thumbnail_pixmap:
            scaled_pixmap = thumbnail_pixmap.scaled(560, 315, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumbnail_label.setPixmap(scaled_pixmap)
        thumbnail_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(thumbnail_label)

        # Video title
        title = self.video_info.get('title', 'Untitled')
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Video info (duration + uploader)
        duration = self.video_info.get('duration', 0)
        duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "N/A"
        uploader = self.video_info.get('uploader', 'Unknown')
        info_label = QLabel(f"Duration: {duration_str} | Channel: {uploader}")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)

        # Quality selection
        quality_group = QGroupBox("Select Quality")
        quality_layout = QVBoxLayout()
        self.quality_button_group = QButtonGroup()

        formats = self.video_info.get('processed_formats', [])
        if formats:
            for i, fmt in enumerate(formats):
                quality = fmt['quality']
                has_audio = " (with audio)" if fmt['has_audio'] else " (video only)"
                radio = QRadioButton(f"{quality}{has_audio}")
                radio.setProperty('format_data', fmt)
                self.quality_button_group.addButton(radio, i)
                quality_layout.addWidget(radio)
                if i == 0:
                    radio.setChecked(True)
        else:
            quality_layout.addWidget(QLabel("No formats available"))

        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)

        # Output format selection
        format_group = QGroupBox("Output Format")
        format_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItem("MP4 (H.264 - Best compatibility)", "mp4")
        self.format_combo.addItem("MKV (Matroska - High quality)", "mkv")
        self.format_combo.addItem("WEBM (VP9 - Web optimized)", "webm")
        self.format_combo.setMinimumHeight(35)
        format_layout.addWidget(self.format_combo)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # FFmpeg status
        status_label = QLabel()
        if self.check_ffmpeg():
            status_label.setText("✓ FFmpeg detected - Video/audio merging available")
            status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        else:
            status_label.setText("⚠ FFmpeg not found - May have issues merging video and audio")
            status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        status_label.setWordWrap(True)
        layout.addWidget(status_label)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        download_btn = QPushButton("Download")
        download_btn.setMinimumHeight(40)
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        download_btn.clicked.connect(self.on_download)
        btn_layout.addWidget(download_btn)
        layout.addLayout(btn_layout)

    def check_ffmpeg(self):
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return shutil.which('ffmpeg') is not None

    def on_download(self):
        checked_button = self.quality_button_group.checkedButton()
        if checked_button:
            fmt = checked_button.property('format_data')
            self.selected_format = fmt
            self.selected_file_format = self.format_combo.currentData()
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Please select a quality option!")

    def get_selection(self):
        if self.selected_format:
            return (self.selected_format['format_id'],
                    self.selected_file_format,
                    self.selected_format['has_audio'])
        return None



class DownloadThread(QThread):
    """
    Thread to download video/playlist without freezing UI
    """
    progress = Signal(int, str)
    finished = Signal(bool, str)

    def __init__(self, url, format_id, output_path, output_format, has_audio, is_playlist=False):
        super().__init__()
        self.url = url
        self.format_id = format_id
        self.output_path = output_path
        self.output_format = output_format
        self.has_audio = has_audio
        self.is_playlist = is_playlist

    def run(self):
        try:
            def progress_hook(d):
                status = d.get('status')
                if status == 'downloading':
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    if total > 0:
                        percent = int((downloaded / total) * 100)
                        speed = d.get('_speed_str') or d.get('speed') or 'N/A'
                        self.progress.emit(percent, f"Downloading: {speed}")
                elif status == 'finished':
                    self.progress.emit(95, "Processing and merging...")

            if self.has_audio:
                fmt = self.format_id
            else:
                fmt = f"{self.format_id}+bestaudio/best"

            outtmpl = os.path.join(self.output_path, '%(title)s.%(ext)s')
            if self.is_playlist:
                outtmpl = os.path.join(self.output_path, '%(playlist_index)s - %(title)s.%(ext)s')

            ydl_opts = {
                'format': fmt,
                'outtmpl': outtmpl,
                'merge_output_format': self.output_format,
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
                'continuedl': True,
                'retries': 10,
                'fragment_retries': 10,
            }

            # Fallback if FFmpeg missing
            if not shutil.which('ffmpeg'):
                self.progress.emit(0, "Warning: FFmpeg not found, using best single-format...")
                ydl_opts['format'] = 'best'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if info.get('_type') == 'playlist' and info.get('entries'):
                    info['entries'] = [e for e in info['entries'] if isinstance(e, dict)]
                ydl.download([self.url])

            self.finished.emit(True, "Download completed successfully!")
        except Exception as e:
            msg = str(e)
            if 'ffmpeg' in msg.lower():
                msg += "\n\nFFmpeg is required for merging video/audio. Install FFmpeg:\nWindows: ffmpeg.org\nLinux: sudo apt install ffmpeg\nMac: brew install ffmpeg"
            self.finished.emit(False, f"Error: {msg}")



class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark_mode = True
        self.network_manager = QNetworkAccessManager()
        self.current_video_info = None
        self.current_thumbnail = None
        self.init_ui()
        self.download_thread = None
        self.info_thread = None

    def init_ui(self):
        self.setWindowTitle("YouTube Downloader")
        self.setMinimumSize(700, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        header_layout = QHBoxLayout()
        title = QLabel("🎬 YouTube Video Downloader")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.theme_btn = QPushButton("☀️ Light Theme")
        self.theme_btn.setMinimumHeight(35)
        self.theme_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_btn)
        main_layout.addLayout(header_layout)

        main_layout.addStretch()

        url_group = QGroupBox("Video URL")
        url_layout = QVBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube video or playlist link here...")
        self.url_input.setMinimumHeight(40)
        url_layout.addWidget(self.url_input)
        url_group.setLayout(url_layout)
        main_layout.addWidget(url_group)

        path_group = QGroupBox("Save Location")
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setText(str(Path.home() / "Downloads"))
        self.path_input.setMinimumHeight(40)
        path_layout.addWidget(self.path_input)
        browse_btn = QPushButton("Browse...")
        browse_btn.setMinimumHeight(40)
        browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(browse_btn)
        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)

        self.download_btn = QPushButton("⬇ Download")
        self.download_btn.setMinimumHeight(50)
        download_font = QFont()
        download_font.setPointSize(14)
        download_font.setBold(True)
        self.download_btn.setFont(download_font)
        self.download_btn.clicked.connect(self.start_process)
        main_layout.addWidget(self.download_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        main_layout.addStretch()
        self.apply_theme()

    # -------------------------
    # Theme methods
    # -------------------------
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        if self.dark_mode:
            self.theme_btn.setText("☀️ Light Theme")
            self.apply_dark_theme()
        else:
            self.theme_btn.setText("🌙 Dark Theme")
            self.apply_light_theme()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #2c3e50; }
            QWidget { background-color: #34495e; color: #ecf0f1; }
            QGroupBox { border: 2px solid #3498db; border-radius: 5px; margin-top: 10px; font-weight: bold; padding: 10px; }
            QLineEdit, QComboBox { background-color: #2c3e50; border: 1px solid #3498db; border-radius: 3px; padding: 5px; color: #ecf0f1; }
            QPushButton { background-color: #3498db; color: white; border: none; border-radius: 3px; padding: 5px; }
        """)
        self.download_btn.setStyleSheet("""
            QPushButton { background-color: #2ecc71; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)

    def apply_light_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QWidget { background-color: #ffffff; color: #2c3e50; }
            QGroupBox { border: 2px solid #3498db; border-radius: 5px; margin-top: 10px; font-weight: bold; padding: 10px; }
            QLineEdit, QComboBox { background-color: #f8f9fa; border: 1px solid #bdc3c7; border-radius: 3px; padding: 5px; color: #2c3e50; }
            QPushButton { background-color: #3498db; color: white; border: none; border-radius: 3px; padding: 5px; }
        """)
        self.download_btn.setStyleSheet("""
            QPushButton { background-color: #2ecc71; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)

    # -------------------------
    # Video ID / thumbnail
    # -------------------------
    def extract_video_id(self, url):
        parsed_url = urlparse(url)
        if 'youtube.com' in parsed_url.netloc:
            query_params = parse_qs(parsed_url.query)
            return query_params.get('v', [None])[0]
        elif 'youtu.be' in parsed_url.netloc:
            return parsed_url.path[1:]
        return None

    def load_thumbnail(self, video_id):
        if not video_id:
            return
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        request = QNetworkRequest(thumbnail_url)
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self.on_thumbnail_loaded(reply))

    def on_thumbnail_loaded(self, reply):
        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.current_thumbnail = pixmap
        reply.deleteLater()

    # -------------------------
    # Browse folder
    # -------------------------
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder to save downloads")
        if folder:
            self.path_input.setText(folder)

    # -------------------------
    # Start process
    # -------------------------
    def start_process(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a video or playlist URL!")
            return
        output_path = self.path_input.text().strip()
        if not output_path:
            QMessageBox.warning(self, "Error", "Please select a save folder!")
            return

        self.status_label.setText("Fetching video information...")
        self.download_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        video_id = self.extract_video_id(url)
        if video_id:
            self.load_thumbnail(video_id)

        self.info_thread = VideoInfoThread(url)
        self.info_thread.info_ready.connect(self.on_info_ready)
        self.info_thread.error.connect(self.on_info_error)
        self.info_thread.start()

    def on_info_ready(self, info):
        self.current_video_info = info
        is_playlist = info.get('_type') == 'playlist' or bool(info.get('entries'))

        if is_playlist:
            title = info.get('title', 'Playlist')
            msg = QMessageBox(self)
            msg.setWindowTitle('Playlist detected')
            msg.setText(f"Detected playlist: {title}\nDo you want to download the entire playlist?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            ret = msg.exec()
            if ret != QMessageBox.Yes:
                self.download_btn.setEnabled(True)
                self.status_label.setText('Download cancelled')
                return

            # Filter only valid dictionary entries
            entries = [e for e in info.get('entries', []) if isinstance(e, dict)]
            if not entries:
                QMessageBox.warning(self, "Error", "No valid videos found in this playlist.")
                self.download_btn.setEnabled(True)
                self.status_label.setText('Download cancelled')
                return

            first_entry = entries[0]
            first_entry['title'] = first_entry.get('title', info.get('title', 'Untitled'))
            first_entry['duration'] = first_entry.get('duration', info.get('duration', 0))
            first_entry['uploader'] = first_entry.get('uploader', info.get('uploader', 'Unknown'))

            dialog = FormatSelectionDialog(first_entry, self.current_thumbnail, self)
            if dialog.exec() == QDialog.Accepted:
                selection = dialog.get_selection()
                if selection:
                    format_id, output_format, has_audio = selection
                    self.start_download(format_id, output_format, has_audio, is_playlist=True)
                    return
                else:
                    self.download_btn.setEnabled(True)
                    self.status_label.setText('Download cancelled')
                    return
            else:
                self.download_btn.setEnabled(True)
                self.status_label.setText('Download cancelled')
                return

        # Single video case
        dialog = FormatSelectionDialog(info, self.current_thumbnail, self)
        if dialog.exec() == QDialog.Accepted:
            selection = dialog.get_selection()
            if selection:
                format_id, output_format, has_audio = selection
                self.start_download(format_id, output_format, has_audio, is_playlist=False)
        else:
            self.download_btn.setEnabled(True)
            self.status_label.setText('Download cancelled')


    def on_info_error(self, error):
        self.status_label.setText("Error fetching video information")
        QMessageBox.critical(self, "Error", error)
        self.download_btn.setEnabled(True)

    # -------------------------
    # Download methods
    # -------------------------
    def start_download(self, format_id, output_format, has_audio, is_playlist=False):
        url = self.url_input.text().strip()
        output_path = self.path_input.text().strip()

        self.status_label.setText("Starting download...")
        self.progress_bar.setValue(0)

        self.download_thread = DownloadThread(url, format_id, output_path, output_format, has_audio, is_playlist=is_playlist)
        self.download_thread.progress.connect(self.on_progress)
        self.download_thread.finished.connect(self.on_finished)
        self.download_thread.start()

    def on_progress(self, percent, message):
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    def on_finished(self, success, message):
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("✓ " + message)
            QMessageBox.information(self, "Success", message)
        else:
            self.progress_bar.setValue(0)
            self.status_label.setText("✗ Download failed")
            QMessageBox.critical(self, "Error", message)
        self.download_btn.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
