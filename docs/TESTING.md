# Checklist uji pengguna

Gunakan [panduan pengguna](USER_GUIDE.md) dari folder proyek yang baru diunduh. Tujuannya memastikan teman yang belum mengenal kode dapat menjalankan tahap verifikasi kandidat. Uji ini belum menilai akurasi sentimen atau kelayakan hubungan revenue.

## Bagian A — tanpa key/internet API

| Langkah | Hasil yang diharapkan |
|---|---|
| Instal requirements.txt dalam .venv | Instalasi berhasil; tidak mengunduh model |
| Jalankan unittest discover | Semua tes selesai dengan OK; HTTP dimock |
| Jalankan prepare-audit dua kali | Pertama created; kedua preserved, data tidak hilang |
| Audit registry awal | Satu kandidat pending, nol included, issues kosong |
| Register link contoh dari panduan | already_registered karena sudah ada di template |
| Register link Short kandidat lain | Satu ID event baru, pending, tanpa tanggal/klasifikasi otomatis |
| Register link yang sama lagi | already_registered; jumlah baris dan catatan lama tidak berubah |
| Coba domain lain atau /watch URL | Ditolak; registry tetap sama |

Jangan menggunakan link/angka rekaan sebagai observasi penelitian. Fixture sintetis hanya tersedia dalam tes otomatis. Catat apakah pesan error dapat dipahami pengguna.

## Bagian B — API metadata, opsional bila key proyek tersedia

1. Masukkan key melalui prompt PowerShell sesuai panduan; nilai tidak boleh muncul pada output.
2. Buat/tinjau konfigurasi privat untuk scope metadata.
3. Jalankan metadata pada kandidat yang dipilih dengan nama paket baru.
4. Pastikan metadata.json dan manifest.json dibuat, dan tidak ada komentar yang diambil.
5. Cocokkan channel ID, timestamp dan judul dengan respons API. Status kanal tidak otomatis menjadi keputusan drip marketing.
6. Coba nama paket yang sama: berkas lama harus tetap utuh; gunakan nama paket baru bila perlu mengulang.

Bagian B belum dijalankan pada komputer Windows teman sebelum ia sendiri mencobanya. Keberhasilan API di cloud tidak menjamin key/jaringan lokal sudah dikonfigurasi dengan benar.

## Bagian C — keputusan manusia dan audit

1. Salin registry ke paket bukti pertama hanya jika belum ada. Gunakan salinan itu secara konsisten.
2. Isi satu kandidat berdasarkan bukti nyata. Jika bukti belum cukup, pertahankan pending.
3. Jalankan audit dengan path registry yang sedang diedit. Periksa jumlah included/pending dan catatan issues.
4. Jika menggunakan Excel, simpan sebagai CSV UTF-8, tutup file, lalu coba register kandidat lain ke registry tersebut; baris lama harus tetap utuh.
5. Simpan catatan penelusuran bulanan dan pemeriksaannya. Jangan mengubah semua bulan menjadi completed tanpa pencarian yang sesuai.
6. Periksa manifest retensi. Jangan menjalankan purge --force pada registry yang masih dibutuhkan.

Jangan sengaja merusak registry kerja nyata untuk pengujian. Gunakan salinan lokal yang aman bila ingin mencoba timestamp salah atau status tidak valid. Pengujian otomatis sudah memiliki kasus sintetis untuk kesalahan tersebut.

## Format laporan teman

Salin format berikut ke pesan/laporan; periksa terlebih dahulu agar tidak berisi key atau data terbatas:

```text
Commit/branch atau tanggal ZIP:
Windows dan versi Python:
Langkah yang dicoba:
Perintah (tanpa key):
Hasil yang diharapkan:
Hasil aktual:
Berhasil/gagal/belum dicoba:
Error yang sudah disunting bila perlu:
Bagian panduan yang membingungkan:
```

Laporkan bagian yang belum dicoba sebagai belum dicoba. Untuk tahap ini, keberhasilan adalah alur registrasi → metadata → keputusan manual → audit dapat dijalankan dan data tersimpan pada tempat yang benar; bukan sekadar tes unit lulus.
