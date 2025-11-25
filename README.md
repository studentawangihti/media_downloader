Flask Universal Downloader

About The Project: Web downloader sederhana namun powerful yang dibangun menggunakan Python Flask. Proyek ini mengatasi masalah umum pada web-based downloader yaitu kompatibilitas format file pada iOS dan manajemen penyimpanan server lokal.

Technical Highlights:
Backend: Python Flask sebagai REST API untuk menangani request download.
Core Engine: Menggunakan yt-dlp untuk ekstraksi stream dan FFmpeg untuk pemrosesan media (merging video+audio, converting to MP3).
Background Tasks: Implementasi Python threading untuk menjalankan tugas pembersihan folder (housekeeping) setiap 60 detik tanpa memblokir main thread.
Frontend: Tampilan responsif dengan Tailwind CSS, dilengkapi log terminal real-time dan indikator proses.
Cross-Platform Handling: Dual-mode download (Direct Stream Copy untuk kecepatan, Re-encode untuk kompatibilitas iOS).

Installation:
Install FFmpeg dan tambahkan ke PATH.
pip install -r requirements.txt
python app.py
