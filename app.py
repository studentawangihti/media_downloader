from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import time
import threading

app = Flask(__name__)
CORS(app)

# 1. Gunakan folder lokal, bukan /tmp
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# 2. Config Khusus iOS (Re-encode ke H.264 + AAC)
IOS_POSTPROCESSOR_ARGS = [
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-strict', 'experimental'
]

def get_opts(format_type, v_qual=None, a_qual=None, ios_mode=False):
    # Base Config
    opts = {
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True,
        # Kita HAPUS 'ffmpeg_location' disini.
        # Sistem akan otomatis mencari ffmpeg di Environment Variables Windows.
    }

    # --- MODE AUDIO ---
    if format_type == 'audio':
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': a_qual if a_qual else '192',
            }]
        })
    
    # --- MODE VIDEO ---
    else:
        # Pilihan Resolusi
        if v_qual and v_qual != 'best':
            format_str = f'bestvideo[height<={v_qual}]+bestaudio/best[height<={v_qual}]'
        else:
            format_str = 'bestvideo+bestaudio/best'

        # Default Container
        opts.update({
            'format': format_str,
            'merge_output_format': 'mp4',
        })

        # JIKA TOMBOL IOS DIKLIK
        if ios_mode:
            # Paksa re-encode berat agar kompatibel iPhone
            opts['postprocessor_args'] = {'merger': IOS_POSTPROCESSOR_ARGS}

    return opts

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')
    if not url: return jsonify({'error': 'URL kosong'}), 400

    try:
        # Cek metadata saja
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Ambil daftar resolusi
            resolutions = set()
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('height'):
                    resolutions.add(f.get('height'))

            metadata = {
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration_string', 'N/A'),
                'uploader': info.get('uploader', 'Unknown'),
                'platform': info.get('extractor_key', 'Unknown'),
                'resolutions': sorted(list(resolutions), reverse=True)
            }
            return jsonify({'status': 'success', 'data': metadata})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    fmt = data.get('format')
    v_qual = data.get('v_quality')
    a_qual = data.get('a_quality')
    ios_mode = data.get('ios_mode', False)

    try:
        opts = get_opts(fmt, v_qual, a_qual, ios_mode)
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if fmt == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            
            clean_name = os.path.basename(filename)
            return send_file(filename, as_attachment=True, download_name=clean_name)

    except Exception as e:
        print(f"Error: {e}") # Print ke terminal laptop biar kelihatan
        return jsonify({'error': str(e)}), 500

# --- FITUR BARU: AUTO DELETE / HOUSEKEEPING ---
def cleanup_files():
    """
    Berjalan di background selamanya.
    Mengecek file setiap 60 detik.
    Menghapus file yang umurnya > 30 menit (1800 detik).
    """
    MAX_AGE_SECONDS = 100 # 30 Menit
    
    while True:
        try:
            now = time.time()
            # Loop semua file di folder downloads
            for filename in os.listdir(DOWNLOAD_FOLDER):
                file_path = os.path.join(DOWNLOAD_FOLDER, filename)
                
                # Pastikan itu file, bukan folder
                if os.path.isfile(file_path):
                    # Cek umur file
                    file_age = now - os.path.getmtime(file_path)
                    
                    if file_age > MAX_AGE_SECONDS:
                        try:
                            os.remove(file_path)
                            print(f"[AUTO-CLEAN] Menghapus file lama: {filename}")
                        except Exception as e:
                            print(f"[ERROR] Gagal hapus {filename}: {e}")
                            
        except Exception as e:
            print(f"[SYSTEM ERROR] Cleanup loop error: {e}")
            
        # Tidur selama 60 detik sebelum cek lagi
        time.sleep(30)

# Jalankan fungsi cleanup di thread terpisah agar tidak memblokir aplikasi utama
cleanup_thread = threading.Thread(target=cleanup_files, daemon=True)
cleanup_thread.start()

# ... (KODE ROUTES /get-info DAN /download TETAP SAMA) ...
if __name__ == '__main__':
    # Host 0.0.0.0 WAJIB agar bisa diakses HP
    app.run(debug=True, host='0.0.0.0', port=5000)