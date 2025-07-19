from flask import Flask, request, render_template, send_file
from yt_dlp import YoutubeDL
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['DOWNLOAD_FOLDER'] = 'downloads'
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

# Initialize database
def init_db():
    conn = sqlite3.connect('videos.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT,
            filepath TEXT,
            audio_path TEXT,
            date_downloaded TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Download video
def download_video(url, quality):
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best',
        'outtmpl': os.path.join(app.config['DOWNLOAD_FOLDER'], '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        },
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4'
        }]
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace('.webm', '.mp4').replace('.mkv', '.mp4')
        return info.get('title', 'No Title'), filename

# Download audio
def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(app.config['DOWNLOAD_FOLDER'], '%(title)s.%(ext)s'),
        'quiet': True,
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        },
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3'
        }]
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = os.path.join(app.config['DOWNLOAD_FOLDER'], info['title'] + ".mp3")
        return filename

@app.route("/", methods=["GET", "POST"])
def index():
    videos = []
    if request.method == "POST":
        url = request.form.get("url")
        quality = request.form.get("quality", "720")

        try:
            title, filepath = download_video(url, quality)
            audio_path = download_audio(url)
            date_downloaded = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            conn = sqlite3.connect('videos.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO videos (title, url, filepath, audio_path, date_downloaded) VALUES (?, ?, ?, ?, ?)",
                (title, url, filepath, audio_path, date_downloaded)
            )
            conn.commit()
            cursor.execute("SELECT * FROM videos ORDER BY id DESC LIMIT 1")
            videos = cursor.fetchall()
            conn.close()
        except Exception as e:
            return f"<h2 style='color:red;'>Error: {e}</h2>"
    return render_template("index.html", videos=videos)

@app.route("/download/<int:video_id>")
def download(video_id):
    conn = sqlite3.connect('videos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM videos WHERE id=?", (video_id,))
    row = cursor.fetchone()
    conn.close()
    if row and os.path.exists(row[0]):
        return send_file(row[0], as_attachment=True)
    return "Video not found", 404

@app.route("/audio/<int:video_id>")
def download_audio_file(video_id):
    conn = sqlite3.connect('videos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT audio_path FROM videos WHERE id=?", (video_id,))
    row = cursor.fetchone()
    conn.close()
    if row and os.path.exists(row[0]):
        return send_file(row[0], as_attachment=True)
    return "Audio not found", 404

# ✅ This block only runs locally (ignored on Render with Gunicorn)
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
