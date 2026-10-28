# Genshin Research Desk

Aplikasi web lokal untuk penelitian mahasiswa: CRUD kandidat Short, verifikasi manusia, pengumpulan komentar YouTube, sentimen pretrained lokal, anotasi/evaluasi, hubungan dengan revenue bulanan, dan forecasting sederhana **eksperimental**.

**[Mulai di sini: panduan teman](docs/PANDUAN_TEMAN.md)** · **[Panduan penggunaan lengkap](docs/USER_GUIDE.md)** · **[Metodologi dan batasan](docs/METHODOLOGY.md)** · **[Checklist uji teman](docs/TESTING.md)**

Hanya Shorts kanal resmi **@GenshinImpact** yang diverifikasi manual sebagai pengumuman awal/drip marketing karakter. Kandidat Januari 2026–September 2026; periode final ditentukan audit. Teaser/demo tidak menggantikan event yang hilang. Waktu pengumuman awal lintas platform dipisahkan dari publikasi Short. API metadata tidak membuktikan format Shorts atau status drip: perlu bukti manual.

Unduh branch `feat/offline-research-foundation`, ekstrak, lalu buka terminal di folder yang berisi file ini. Gunakan Python 3.12 yang telah diuji.

```powershell
python setup_project.py
python run.py
```

Instalasi pertama memasang PyTorch CPU dan dependensi; membutuhkan internet serta ruang disk beberapa GB. Buka `http://127.0.0.1:5000` di browser pada komputer yang sama. Pada Windows, setelah instalasi, aplikasi juga dapat dijalankan dengan klik ganda **run.bat**. Terminal server tetap dibuka; Ctrl+C menghentikannya. Jika port terpakai: `python run.py --port 5001`.

**Tidak perlu mengetik link satu per satu di PowerShell.** Gunakan halaman Kandidat & verifikasi di browser. API key diisi pada Pengaturan & API, hanya tersimpan di memori server; jangan menaruh key di Git, CSV atau chat. Environment `YOUTUBE_API_KEY` tetap didukung. `.env` tidak dimuat otomatis.

Menu **Panduan untuk teman** menjelaskan pengisian pengaturan, input link, verifikasi manusia, dan pengambilan komentar otomatis. Jika langkah diblokir, halaman error menunjukkan pengaturan yang belum lengkap dan tombol langsung ke Pengaturan & API. **Retensi 1–30 hari** adalah batas penyimpanan paket data; **jendela 72 jam** menentukan komentar yang dianalisis.

## Alur aplikasi

1. **Pengaturan & API:** masukkan key dan dokumentasikan dasar penggunaan serta scope yang berlaku. Default offline/dry-run; tidak ada pengumpulan otomatis.
2. **Kandidat & verifikasi:** tambah, baca, edit, atau hapus kandidat melalui form. Ambil metadata API, lalu manusia memutuskan apakah konten benar pengumuman awal/drip marketing. Periode Januari–September 2026. Tanpa impor massal link, sesuai keputusan pengguna.
3. **Cakupan bulanan:** catat penelusuran tiap bulan dan event tanpa Short yang sesuai.
4. **Komentar & NLP:** pilih pilot temporal atau seluruh event included, kumpulkan komentar utama, lalu jalankan model lokal. Progres ditampilkan di browser. Pagination terputus tidak masuk analisis utama.
5. **Anotasi dan evaluasi:** sampel hingga 200 komentar, tiga kelas, prediksi disembunyikan saat anotasi, macro-F1, confusion matrix dan Cohen κ bila tersedia dua anotator.
6. **Revenue:** isi satu seri konsisten lewat form bulanan atau impor CSV manual. Angka tidak diambil atau dikarang otomatis.
7. **Analisis:** agregasi akhir jendela 72 jam bulan t → revenue t+1, Spearman dan scatter berlabel bulan. Forecasting Ridge dibandingkan baseline naïf, hanya berjalan bila pemeriksaan data terpenuhi.

## Batas interpretasi

Bukan analisis kausal dan komentator tidak mewakili seluruh pemain/pembayar. Likes saat pengambilan bukan bobot historis. Data retrospektif tidak merekonstruksi komentar yang telah dihapus. Forecasting dapat berstatus **blocked**; itu hasil pemeriksaan kelayakan, bukan bukti aplikasi gagal. Dataset Januari–September dapat terlalu kecil untuk prediksi yang dapat diandalkan.

Model: `cardiffnlp/twitter-roberta-base-sentiment-latest`, revision tetap, CC-BY-4.0; catatan sumber dan checksum terdapat di metodologi. Bobot sekitar 500 MB diunduh saat NLP pertama, kemudian dipakai lokal. Tidak ada fine-tuning atau pengiriman teks komentar ke layanan AI eksternal.

## Penyimpanan

Proyek browser berada di `data/workbench/`. Saat pertama kali dibuat, aplikasi menyalin registry/coverage lama dari data/ jika tersedia; berkas sumber tidak ditimpa. Sesudah itu edit data melalui aplikasi. Key tidak ditulis ke pengaturan. Paket komentar, label, anotasi dan grafik mengikuti manifest maksimum 30 hari; metadata event mempunyai tanggal kedaluwarsa sendiri. Penghapusan event juga menghapus dataset yang bergantung padanya. Ekspor/cadangan di luar aplikasi harus dikelola sendiri.

Aplikasi untuk satu pengguna lokal; teman menjalankan salinan sendiri. Mode debug mati dan server hanya mengikat loopback. Jangan menaruh data nyata atau key ke Git. Tidak disediakan dashboard publik atau sistem akun bersama.

## Tes dan CLI

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tes otomatis menggunakan fixture sintetis dan API/model mock. Tidak mengambil komentar nyata atau membuktikan akurasi model pada data penelitian. Tes gaya opsional: instal requirements-dev.txt lalu jalankan ruff check/format --check untuk genshin_research.

CLI lama prepare-audit, register, metadata, audit, purge tetap tersedia. CLI web: `.\.venv\Scripts\python.exe -m genshin_research serve`. Untuk pekerjaan harian gunakan browser dan [panduan pengguna](docs/USER_GUIDE.md).
