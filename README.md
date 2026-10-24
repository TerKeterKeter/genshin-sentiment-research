# Genshin sentiment research

Fondasi penelitian mahasiswa: “Bagaimana sentimen komentar awal terhadap pengumuman karakter Genshin Impact, dan apakah agregat sentimen tersebut berhubungan dengan estimasi pendapatan mobile pada bulan berikutnya?”

## Batas penelitian

Hanya Shorts kanal resmi **@GenshinImpact** yang diverifikasi manual sebagai pengumuman awal/drip marketing karakter. Kandidat Januari 2024–September 2026; periode final ditentukan audit. Teaser/demo tidak menggantikan event yang hilang. Waktu pengumuman awal lintas platform dipisahkan dari publikasi Short. API metadata tidak membuktikan format Shorts atau status drip: perlu bukti manual.

Komentar utama berbahasa Inggris dalam `[publikasi, publikasi + 72 jam)`, tanpa balasan. Komentar diedit pada/selepas cutoff dikeluarkan secara konservatif; likes saat pengambilan bukan bobot historis. Bahasa otomatis bisa salah, khususnya teks pendek/emoji: tinjau sampel bahasa dan laporkan jumlah bahasa lain serta tidak teridentifikasi. Spam/teks identik ditandai untuk tinjauan, tidak otomatis dibuang.

Unit hubungan ekonomi **bulan**, bukan komentar. Bulan ditentukan saat jendela 72 jam selesai; agregat komentar dihitung dengan bobot komentar sama (event dengan banyak komentar lebih dominan). Revenue dipasangkan ke bulan berikutnya. Tidak ada forecasting, fine-tuning, antusiasme, pull intention, atau prediksi per karakter.

## Instalasi dan validasi offline

Python 3.12 disarankan. Dari root repositori:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m genshin_research audit
```

Pengujian inti dan audit juga berjalan dengan Python standar tanpa instalasi paket. Notebook memerlukan paket analisis. Versi dependensi dipatok langsung; belum merupakan lock lengkap beserta hash. Torch CPU cukup untuk inferensi; unduhan model baru dilakukan saat inferensi yang diizinkan.

## Langkah bertahap

1. Isi `templates/events.csv` atau salin ke `data/events.csv`. Status: `pending`, `included`, `excluded`, `no_matching_short`. Isi alasan pengecualian. Gunakan `content_type=verified_initial_drip_short` hanya setelah verifikasi manual dan API. Jangan mengisi tanggal dari tebakan.
2. Lengkapi pemeriksaan kebijakan dan izin di [panduan data](docs/data-management.md). Default `dry_run=true` memblokir semua operasi data nyata. `.env.example` hanya dokumentasi; CLI membaca variabel proses, tidak otomatis memuat `.env`.
3. Setelah izin pengumpulan terdokumentasi, `export YOUTUBE_API_KEY=...` di shell privat dan gunakan `python -m genshin_research metadata -- -2um93gmb3A` (ID diawali tanda minus). Cocokkan channel ID dengan identitas kanal resmi, catat judul/timestamp persis API dan bukti pengumuman awal. Opsi `metadata --refresh -- VIDEO_ID` mengambil ulang metadata tanpa memperpanjang izin turunan.
4. Jalankan `python -m genshin_research audit --events data/events.csv --revenue data/revenue.csv`. `pilot --events data/events.csv` memilih 6–10 event merata menurut waktu; periksa distribusi tahun tanpa melihat sentimen/revenue.
5. `collect --events data/pilot.csv --package data/pilot_run_01` mengambil seluruh pagination, menyaring waktu lokal, menduplikasi berdasarkan ID, dan menyimpan status lengkap/terputus. Tidak ada filter tanggal endpoint atau early-stop yang diasumsikan. Pengambilan terputus tidak boleh masuk analisis utama; buat paket baru untuk pengambilan ulang.
6. Verifikasi model card `cardiffnlp/twitter-roberta-base-sentiment-latest`: simpan immutable commit SHA, lisensi aktual, serta pemetaan negative/neutral/positive di `config.json` dan catatan model. Model belum diunduh/diverifikasi. Kemudian `nlp --package data/pilot_run_01` melakukan normalisasi NFC/whitespace, identifikasi bahasa, dan inferensi lokal CPU. Negasi/emoji dipertahankan; pemotongan input panjang ditandai. Domain Twitter berbeda dari YouTube.
7. `annotate --package data/pilot_run_01 --events data/pilot.csv` menghasilkan sekitar 200 komentar dengan sampling acak berstrata event × interval 24 jam (seed 42, alokasi seimbang hingga kapasitas strata). Isi label manual sesuai [panduan](docs/annotation.md), lalu `evaluate --package data/pilot_run_01`. Jangan mengisi gold dengan output model.
8. Impor revenue manual dari satu seri sumber ke template; jangan mengarang nilai. `analyze --package data/pilot_run_01 --events data/pilot.csv --revenue data/revenue.csv` menulis agregat, pasangan, scatter berlabel bulan dan Spearman. Izin penggabungan eksternal terpisah wajib. Notebook menunjukkan eksplorasi offline sintetis dan langkah inspeksi.

Semua subperintah memakai awalan `python -m genshin_research`; jalankan `--help` untuk argumen. Opsi global `--config` dan `--permissions` diletakkan sebelum subperintah.

## Status audit awal

Satu kandidat terdaftar: https://youtube.com/shorts/-2um93gmb3A. **Nol event terverifikasi**, bukan bukti bahwa tidak ada event yang memenuhi kriteria. Judul, karakter, channel ID, timestamp dan distribusi bulan/tahun belum dapat ditetapkan. Belum ada revenue, pasangan aktual **0**. Event tanpa Short belum diaudit. Dataset belum dapat dinyatakan layak. Audit tidak mencari seluruh katalog kanal otomatis; registry harus dilengkapi manual sebelum menyimpulkan cakupan.

API key belum tersedia. Akses dua halaman kebijakan resmi pada sesi setup ditolak proxy HTTP 403; isi kebijakan terbaru belum diverifikasi. Tidak ada pengumpulan komentar/model/revenue nyata atau hasil sentimen empiris dalam repositori.

## Keterbatasan

Retrospeksi hanya melihat komentar yang masih dapat diakses; komentar dihapus/privat/moderasi tidak merekonstruksi kondisi historis. Komentator bukan representasi seluruh pemain atau pembayar. Hubungan bukan kausal: tren waktu, update game, rerun banner, serta beda cakupan audiens dan revenue dapat memengaruhi hasil. Spearman/p-value bersifat eksploratif; ketergantungan temporal dan jumlah bulan kecil melemahkan inferensi. Bulan tanpa event berbeda dari nol komentar dan net sentiment nol. Tidak menggandakan revenue ke tiap komentar.

Kesiapan forecasting tetap ditunda: nilai jumlah bulan independen, pola missingness, cakupan sumber, dan fitur yang benar-benar tersedia sebelum waktu prediksi; tidak ada ambang minimum universal yang menjamin kelayakan.

## Pemeriksaan sebelum push

Aktifkan virtual environment, lalu jalankan `bash scripts/check.sh`. GitHub Actions menjalankan tes sintetis dan audit tanpa API key; dependensi model besar tidak diunduh di CI. Hasil CI baru diketahui setelah workflow berjalan di GitHub.

Simpan API key sebagai environment variable privat. `.env`, variasi `.env.*` (kecuali contoh kosong), `config.local.json`, `permissions.local.json`, data dan output lokal diabaikan Git. Jangan menulis key di konfigurasi yang dilacak. Untuk konfigurasi izin lokal gunakan `python -m genshin_research --config config.local.json --permissions permissions.local.json SUBCOMMAND`.
