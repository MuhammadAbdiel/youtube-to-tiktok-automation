# YouTube to TikTok Automation

Sistem automasi untuk mengkonversi video YouTube menjadi konten TikTok dengan subtitle otomatis.

## Struktur File

```
├── main.py                 # File utama untuk menjalankan automasi
├── config.py              # Manajemen konfigurasi
├── video_downloader.py    # Download video dari YouTube
├── video_processor.py     # Pemrosesan video, transkripsi, dan editing
├── tiktok_uploader.py     # Upload ke TikTok
├── install.py             # Script instalasi dependencies
├── requirements.txt       # Dependencies Python
├── .env                   # Variabel environment (buat manual)
└── README.md              # File ini
```

## Setup

### Metode 1: Instalasi Otomatis

```bash
python install.py
```

### Metode 2: Instalasi Manual

1. **Update pip dan install dependencies**

   ```bash
   pip install --upgrade pip
   pip install --upgrade pytube
   pip install -r requirements.txt
   ```

2. **Buat File .env**
   Buat file `.env` di root directory dengan isi:

   ```env
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here

   # Google Account Configuration
   GOOGLE_EMAIL=your_google_email@gmail.com
   GOOGLE_PASSWORD=your_google_password

   # Paths Configuration
   DOWNLOAD_PATH=./downloads
   OUTPUT_PATH=./output

   # Video Processing Configuration
   CLIP_DURATION=60
   MAX_CLIPS_PER_VIDEO=5
   ```

3. **Jalankan Aplikasi**
   ```bash
   python main.py
   ```

## Fitur

- **Monitoring YouTube**: Memantau channel YouTube yang dikonfigurasi
- **Download Otomatis**: Download video baru dari channel yang dipantau
- **Transkripsi AI**: Menggunakan Whisper untuk transkripsi audio
- **Segmentasi Cerdas**: AI menentukan bagian video yang menarik
- **Video Vertikal**: Konversi ke format 9:16 untuk TikTok
- **Subtitle Otomatis**: Menambahkan subtitle pada video
- **Upload Otomatis**: Upload ke TikTok dengan metadata yang dioptimasi

## Konfigurasi Channel

Edit file `config.json` untuk menambah/mengubah channel yang dipantau:

```json
{
  "channels": {
    "Timothy Ronald": {
      "channel_id": "UCXMB8OiiSnq2B4xLgUtTYhw",
      "rss_url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCXMB8OiiSnq2B4xLgUtTYhw"
    }
  }
}
```

## Troubleshooting

### Error Download Video (HTTP 400/403)

Jika mendapat error saat download video, coba solusi berikut:

1. **Update pytube ke versi terbaru:**

   ```bash
   pip install --upgrade pytube
   ```

2. **Install yt-dlp sebagai backup:**

   ```bash
   pip install --upgrade yt-dlp
   ```

3. **Clear cache dan restart:**

   ```bash
   pip cache purge
   python main.py
   ```

4. **Jika masih error, coba manual download untuk test:**
   ```bash
   python -c "from pytube import YouTube; print(YouTube('https://www.youtube.com/watch?v=VIDEO_ID').title)"
   ```

### Error Login TikTok

1. **Clear browser data:**

   - Hapus folder `chrome_user_data`
   - Restart aplikasi

2. **Disable 2FA sementara** pada akun Google

3. **Gunakan App Password** jika menggunakan 2FA

### Error Dependencies

```bash
# Reinstall semua dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### Performance Issues

1. **Reduce video quality dalam config:**

   ```json
   {
     "clip_duration": 30,
     "max_clips_per_video": 3
   }
   ```

2. **Increase delays** antara uploads

## Requirements

- Python 3.8+
- Chrome/Chromium browser
- ChromeDriver (akan di-download otomatis oleh Selenium)
- OpenAI API Key
- Google Account untuk login TikTok

## Error Handling

Sistem memiliki built-in error handling:

- **Retry mechanism** untuk download yang gagal
- **Fallback ke yt-dlp** jika pytube gagal
- **Auto cleanup** file temporary
- **Skip video** yang error dan lanjut ke berikutnya
