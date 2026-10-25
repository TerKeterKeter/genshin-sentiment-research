# Genshin sentiment research

Paket uji CLI untuk **registrasi dan verifikasi manual** kandidat Shorts drip marketing karakter Genshin Impact dari kanal resmi @GenshinImpact, Januari–September 2026.

**Mulai dari [panduan pengguna lengkap](docs/USER_GUIDE.md).** Panduan menjelaskan instalasi Windows/PowerShell, tempat API key, input link, metadata, setiap kolom verifikasi manual, audit hasil, retensi, serta solusi error umum. Untuk teman yang mencoba, gunakan [checklist dan format laporan tes](docs/TESTING.md).

## Instalasi singkat — PowerShell

Dari folder yang berisi file ini:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m genshin_research prepare-audit
.\.venv\Scripts\python.exe -m genshin_research audit
```

Python 3.12 disarankan. Pemanggilan langsung Python .venv tidak memerlukan aktivasi PowerShell. macOS/Linux memakai python3 untuk membuat .venv dan .venv/bin/python untuk menjalankan perintah berikutnya. Tes memakai fixture sintetis/HTTP mock tanpa API key atau kuota.

## Alur pengguna

1. prepare-audit membuat registry dan catatan penelusuran di data/ tanpa menimpa file yang sudah ada.
2. register menerima link Short/ID dan nama karakter opsional; ID event otomatis, status pending. Link sama tidak menggandakan baris.
3. metadata membaca judul, waktu publikasi dan channel ID melalui API. Aktifkan scope metadata dan environment YOUTUBE_API_KEY secara privat sesuai panduan. Simpan hasil ke paket lokal dengan manifest retensi.
4. Manusia menonton konten dan memeriksa bukti pengumuman awal lintas platform, lalu mengisi registry. API tidak mengklasifikasikan drip marketing.
5. audit memeriksa kelengkapan data dan merangkum keputusan manual serta penelusuran bulanan. purge tersedia untuk paket kedaluwarsa.

Contoh registrasi offline:

```powershell
.\.venv\Scripts\python.exe -m genshin_research register "https://youtube.com/shorts/-2um93gmb3A" --character "Linnea"
```

Link contoh sudah ada di template, sehingga already_registered adalah hasil yang wajar. Ganti link untuk kandidat baru. Semua instruksi pengisian dan perintah API ada di [panduan pengguna](docs/USER_GUIDE.md).

## Batas tahap ini

Hanya Shorts yang diverifikasi manusia sebagai pengumuman awal/drip marketing dapat dimasukkan. Teaser/demo tidak menggantikan event yang hilang. Waktu pengumuman lintas platform dipisahkan dari publikasi Short; tanggal publikasi harus berasal dari API. Default offline/dry-run. Data, key dan konfigurasi privat tidak dimasukkan ke Git.

Versi ini belum mengambil komentar atau menganalisis sentimen/revenue. Setelah audit manual dan kelayakan dataset selesai, tahap berikutnya dapat dibangun: komentar utama Inggris dalam 72 jam pertama, tiga kelas sentimen memakai model pretrained lokal, evaluasi manual, dan agregat akhir-jendela bulan t dipasangkan dengan estimasi mobile revenue t+1 dari satu seri konsisten. Implementasi terdahulu tersedia dalam riwayat Git, misalnya ee3b941.

Hubungan tersebut eksploratif, bukan kausal. Komentator bukan representasi seluruh pemain/pembayar; data retrospektif tidak merekonstruksi komentar yang dihapus. Perbedaan cakupan audiens/revenue, tren, update dan rerun perlu dipertimbangkan; forecasting ditunda.

## Pemeriksaan pengembang

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m ruff check genshin_research
.\.venv\Scripts\python.exe -m ruff format --check genshin_research
```

GitHub Actions menjalankan tes offline dan pemeriksaan gaya. [Catatan kebijakan](docs/policy-review.md) tetap menjadi rujukan batas penggunaan data. [Panduan metadata lama](docs/metadata-audit.md) mengarah ke panduan pengguna yang sama.
