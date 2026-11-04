# Checklist trial aplikasi

Mulai dari [panduan untuk teman](PANDUAN_TEMAN.md); detail lanjutan ada di [panduan pengguna](USER_GUIDE.md). Bagikan tautan branch/ZIP, jangan data pribadi atau key.

## A. Instalasi dan CRUD browser

- Jalankan python setup_project.py, lalu python run.py. Halaman ringkasan muncul pada localhost.
- Default offline aktif. Buka semua menu tanpa key: ringkasan, kandidat, cakupan, dataset, revenue, pengaturan, panduan untuk teman.
- Dengan pengaturan penggunaan belum lengkap, coba tombol metadata. Error harus menyebut butir yang belum terpenuhi dan menyediakan tautan Pengaturan; tidak ada panggilan API. Lengkapi catatan yang benar dan simpan sebelum mencoba ulang.
- Tambah satu link Short, buka detail, edit nama/catatan, simpan. Duplikat ditolak tanpa menambah baris.
- Ganti link: metadata lama dikosongkan dan status kembali pending.
- Catat pengumuman tanpa Short dengan nama saja, lalu no_matching_short dan alasan.
- Uji hapus hanya pada kandidat uji yang memang boleh dihapus; konfirmasi dibutuhkan. Jangan hapus data kerja demi tes.
- Tutup dan jalankan ulang server: data tetap ada; key yang dimasukkan melalui browser harus diisi lagi.

## B. Metadata dan koleksi nyata, bila scope proyek tersedia

- Isi key di Pengaturan, tanggal/referensi scope, dan matikan offline hanya untuk operasi yang diizinkan.
- Ambil metadata satu kandidat. Channel ID/timestamp berasal dari API; included tetap memerlukan keputusan manusia.
- Lengkapi sumber pengumuman awal, jenis konten dan catatan. Kandidat tanpa bukti tidak dapat menjadi included.
- Pilih semua event untuk uji kecil atau pilot temporal ketika minimal enam tersedia.
- Mulai pengumpulan. Progres tampil dan dataset menyimpan jumlah halaman, deduplikasi, lengkap/terputus, serta expiry.
- Jangan membuat klaim kesiapan jika API/key/kuota belum diuji. Dataset terputus harus diblokir dari NLP/analisis utama.

## C. Sentimen, anotasi dan revenue

- Jalankan NLP. Unduhan model pertama sekitar 500 MB; periksa bahwa masalah jaringan menghasilkan pesan yang jelas. Jangan menonaktifkan TLS atau checksum.
- Baca jumlah non-English/undetermined, edited-after-cutoff, duplikasi/spam dan truncation.
- Buat sampel anotasi, isi label tanpa melihat prediksi, simpan per halaman. Jika dua anotator, kerjakan independen.
- Evaluasi: cek n gold, macro-F1, confusion matrix dan agreement. Gold kosong harus ditolak.
- Isi/upload satu seri revenue yang provenance/cakupannya sudah diperiksa. Bulan duplikat/cakupan campuran harus ditolak.
- Jalankan analisis: jumlah pasangan aktual, missing reasons dan scatter bulanan tersedia. Sampel satu event tidak otomatis menghasilkan korelasi.
- Jalankan forecast: blocked pada data kecil/missing timing adalah hasil yang benar. Jika berjalan, cek urutan waktu, MAE terhadap baseline, serta label nowcast/forecast yang tepat.

## D. Otomasi yang tersedia

`.venv` Python menjalankan `-m unittest discover -s tests -v`. Fixture sintetis/HTTP dan classifier mock menguji CRUD → metadata → koleksi → NLP → anotasi → evaluasi → analisis → penolakan forecast, serta fungsi forecasting pada seri sintetis yang memenuhi pemeriksaan. Pengujian ini tidak membuktikan akurasi empiris model.

Server HTTP nyata dan metadata read-only dapat diuji terpisah. Uji browser di Windows dan pengumpulan/analisis data penelitian harus dicatat tersendiri; jangan menyebut langkah belum dicoba sebagai lulus. Tidak ada demo data palsu yang disajikan sebagai hasil penelitian.

## Format laporan teman

```text
Commit/branch atau tanggal ZIP:
OS dan versi Python:
Langkah/menu yang dicoba:
Hasil yang diharapkan:
Hasil aktual:
Lulus/gagal/belum dicoba:
Pesan error (tanpa key atau data terbatas):
Bagian panduan/UI yang membingungkan:
```

Jangan kirim API key, cookie sesi, komentar mentah, identitas sampel atau data terbatas dalam screenshot/laporan. Berkas ekspor dan backup tetap mengikuti retensi.

## Bukti validasi pengembangan saat penyerahan

Pada 28 Oktober 2026 (Asia/Jakarta), **41 tes offline lulus**, termasuk perbaikan installer tanpa pip dan pengujian pesan pengaturan: hanya butir yang belum lengkap ditampilkan, permintaan API belum dijalankan saat diblokir, dan metadata dapat dicoba ulang setelah pengaturan disimpan tanpa mengaktifkan operasi lain. Menu panduan dan pemeriksaan gaya Python juga lulus. Ini tidak mencatat uji baru terhadap pengumpulan komentar nyata atau inferensi dengan bobot sebenarnya.

Pada 26 Oktober 2026 (Asia/Jakarta), 35 tes otomatis lulus; pemeriksaan gaya dan sintaks JavaScript lulus. Alur browser melalui Flask test client memakai data sintetis serta API/classifier mock. Server HTTP nyata, CRUD, dan satu metadata kandidat read-only lewat YouTube API juga berhasil; tidak ada komentar penelitian yang dikumpulkan untuk validasi ini. Installer dapat diulang pada Linux dan launcher python run.py berhasil menyajikan halaman offline.

Model card, revision, label dan checksum bobot diverifikasi dari sumber resmi. Inferensi dengan bobot sebenarnya **belum berhasil dijalankan di cloud**: unduhan ditolak HTTP 403 pada CDN us.aws.cdn.hf.co. Domain tersebut ditambahkan ke draft jaringan, tetapi saving draft tidak menerapkannya ke runtime; perlu review/simpan/publish pengaturan. Pengujian native Windows dan inferensi bobot pada komputer teman masih perlu dicatat sebagai belum dicoba sampai benar-benar dijalankan. Model mock tidak diperlakukan sebagai bukti akurasi/runtime pretrained.
