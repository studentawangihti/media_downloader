from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import time

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# --- FUNGSI 1: Ambil Info & Deteksi Resolusi ---
@app.route('/get-info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL kosong'}), 400

    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Deteksi resolusi yang tersedia (Khusus Video)
            formats = info.get('formats', [])
            resolutions = set()
            for f in formats:
                # Ambil tinggi video (height) jika ada (cth: 1080, 720)
                if f.get('vcodec') != 'none' and f.get('height'):
                    resolutions.add(f.get('height'))
            
            # Urutkan resolusi dari besar ke kecil
            sorted_res = sorted(list(resolutions), reverse=True)

            metadata = {
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration_string', 'N/A'),
                'uploader': info.get('uploader', 'Unknown'),
                'platform': info.get('extractor_key', 'Unknown'),
                'resolutions': sorted_res # Kirim daftar resolusi ke frontend
            }
            return jsonify({'status': 'success', 'data': metadata})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- FUNGSI 2: Download dengan Kualitas ---
@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    fmt = data.get('format')      # 'merge', 'audio', 'video_only'
    v_qual = data.get('v_quality') # Contoh: 1080, 720, atau 'best'
    a_qual = data.get('a_quality') # Contoh: '128', '192', '320'

    try:
        # --- LOGIKA KONFIGURASI KUALITAS ---
        
        # Default format string
        format_str = 'bestvideo+bestaudio/best'
        
        # Jika user minta Video dengan resolusi tertentu
        if fmt in ['merge', 'video_only'] and v_qual != 'best':
            # Logic: Cari video terbaik yang tingginya TIDAK LEBIH dari v_qual
            # Ini aman: jika minta 1080 tapi video cuma ada 720, dia kasih 720.
            if fmt == 'merge':
                format_str = f'bestvideo[height<={v_qual}]+bestaudio/best[height<={v_qual}]'
            else:
                format_str = f'bestvideo[height<={v_qual}]'

        # Konfigurasi Audio (Bitrate)
        # Kita atur via postprocessor args FFmpeg
        postprocessors = []
        if fmt == 'audio':
            format_str = 'bestaudio/best'
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': a_qual if a_qual else '192',
            }]

        opts = {
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'format': format_str,
            'postprocessors': postprocessors
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if fmt == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            
            clean_name = os.path.basename(filename)
            return send_file(filename, as_attachment=True, download_name=clean_name)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # app.run(debug=True, port=5000)
    app.run(debug=True, host='0.0.0.0', port=5000)