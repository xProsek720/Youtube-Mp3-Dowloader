from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QComboBox, QLabel, QFileDialog, QProgressBar, QMessageBox
from PyQt5.QtCore import QTimer
import threading
import subprocess
import sys
import os
from pytube import YouTube, Playlist

# Shared variables for thread communication
download_progress = 0
total_videos = 0
downloaded_count = 0
current_video_index = 0  # Index of the currently downloading/converting video
download_message = ""

def show_save_dialog():
    path = QFileDialog.getExistingDirectory(window, "Select Directory")
    path_label.setText(path)
    return path

def download_video():
    global total_videos, downloaded_count, download_message
    url = url_input.text()
    output_path = path_label.text()
    if not url:
        print("URL is empty!")
        return
    # Reset state for new download
    total_videos = 0
    downloaded_count = 0
    download_message = ""
    # Start the download in a new thread
    thread = threading.Thread(target=download_videos_thread, args=(url, output_path))
    thread.start()


def download_videos_thread(url, output_path):
    global total_videos, downloaded_count, download_message, current_video_index
    try:
        if "playlist" in url:
            playlist = Playlist(url)
            total_videos = len(playlist.video_urls)
        else:
            total_videos = 1

        current_video_index = 0
        download_message = ""
        if "playlist" in url:
            for video in playlist.videos:
                download_and_convert(video.watch_url, output_path)
                current_video_index += 1
        else:
            download_and_convert(url, output_path)
        download_message = "Download completed!"
    except Exception as e:
        download_message = f"Error: {str(e)}"

def download_and_convert(url, output_path):
    global downloaded_count
    yt = YouTube(url, on_progress_callback=progress_function)
    if format_box.currentText() == 'MP4':
        stream = yt.streams.filter(file_extension='mp4', resolution=quality_box.currentText() if quality_box.currentText() != 'Best' else None).first()
    else:  # MP3 or FLAC
        stream = yt.streams.filter(only_audio=True).first()
    file_path = stream.download(output_path=output_path)
    downloaded_count += 1
    if format_box.currentText() == 'MP3':
        convert_to_mp3(file_path)

def progress_function(stream, chunk, bytes_remaining):
    global download_progress
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    partial_progress = int((bytes_downloaded / total_size) * 50)  # 50% for download part
    download_progress = (current_video_index * 100 + partial_progress) / total_videos

def convert_to_mp3(file_path):
    global download_progress
    output_path = file_path.rsplit('.', 1)[0] + '.mp3'
    command = ['ffmpeg', '-y', '-i', file_path, '-vn', '-ar', '44100', '-ac', '2', '-b:a', '320k', output_path]
    try:
        subprocess.run(command, check=True)
        os.remove(file_path)  # Remove the original file after conversion
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert file: {e}")
    # Assume conversion takes the remaining 50% of the progress for this file
    download_progress += 50 / total_videos

def update_gui():
    global download_message  # Ensure access to the global variable
    progress_bar.setValue(int(download_progress))
    download_counter_label.setText(f"Downloads: {downloaded_count}/{total_videos}")
    if download_message:
        QMessageBox.information(window, "Download Status", download_message)
        download_message = ""  # Clear the message after showing it

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle('YouTube Downloader')

layout = QVBoxLayout()
url_input = QLineEdit()
url_input.setPlaceholderText("Enter YouTube URL or Playlist URL here")
path_label = QLabel("No path selected")
path_button = QPushButton("Choose Path")
path_button.clicked.connect(show_save_dialog)
format_box = QComboBox()
format_box.addItems(['MP4', 'MP3', 'FLAC'])
quality_box = QComboBox()
quality_box.addItems(['Best', '144p', '240p', '360p', '480p', '720p', '1080p'])
download_button = QPushButton('Download')
download_button.clicked.connect(download_video)
progress_bar = QProgressBar()
download_counter_label = QLabel("Downloads: 0/0")
layout.addWidget(QLabel("Enter URL:"))
layout.addWidget(url_input)
layout.addWidget(QLabel("Output Path:"))
path_layout = QHBoxLayout()
path_layout.addWidget(path_label)
path_layout.addWidget(path_button)
layout.addLayout(path_layout)
layout.addWidget(QLabel("Select Format:"))
layout.addWidget(format_box)
layout.addWidget(QLabel("Select Quality:"))
layout.addWidget(quality_box)
layout.addWidget(download_button)
layout.addWidget(progress_bar)
layout.addWidget(download_counter_label)
window.setLayout(layout)
window.show()

timer = QTimer()
timer.timeout.connect(update_gui)
timer.start(100)  # Update every 100 ms

sys.exit(app.exec_())
