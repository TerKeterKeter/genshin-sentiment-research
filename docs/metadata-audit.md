# Verifikasi metadata kandidat

Perintah metadata hanya memakai videos.list dan channels.list untuk membaca judul, waktu publikasi, durasi dan mencocokkan channel ID dengan handle resmi. Perintah ini tidak mengambil komentar dan tidak menghitung sentimen. Pemeriksaan metadata biasa dipisahkan dari additional derived metrics; pengecualian akademik terhadap kebijakan sentimen tetap belum dibuktikan.

## Konfigurasi lokal

API key cloud tidak otomatis tersedia di komputer Windows. Sediakan YOUTUBE_API_KEY melalui environment lokal yang privat. Jangan menaruh key dalam JSON, CSV atau Git.

Buat config.local.json dari config.json, lalu set dry_run=false. Gunakan permissions.local.json dengan scope berikut setelah meninjau kebijakan akses metadata dan mengonfirmasi tujuan penggunaan:

```json
{
  "policy_review_status": "documented",
  "policy_reviewed_at": "2026-10-25",
  "evidence_reference": "Read-only metadata audit; docs/metadata-audit.md and docs/policy-review.md",
  "metadata_allowed": true,
  "retention_days": 30
}
```

Isi tanggal pemeriksaan aktual. Ini mencatat scope pembacaan metadata, bukan persetujuan sentiment/komentar. Pertahankan konfigurasi privat yang sudah ada; jangan menimpanya secara membabi buta. Default file yang dilacak tetap dry-run dan semua operasi nyata dinonaktifkan.

## Ambil dan simpan bukti API

```powershell
python -m genshin_research --config config.local.json --permissions permissions.local.json metadata --package data/metadata_candidate_001 -- -2um93gmb3A
```

`--` diperlukan karena ID video diawali minus. Nama paket harus baru; perintah tidak menimpa bukti sebelumnya. Paket menyimpan metadata.json dan manifest.json dengan waktu kedaluwarsa. Setiap pemanggilan mengambil metadata terbaru; untuk refresh gunakan nama paket baru dan purge paket lama. Tidak ada flag tambahan yang membuka pengumpulan komentar.

```powershell
python -m genshin_research purge --package data/metadata_candidate_001
```

Purge tanpa --force menghapus paket setelah kedaluwarsa; gunakan --force bila perlu menghapus segera. Jangan menyalin metadata ke Git atau ke luar inventaris retensi.

## Tinjau kelayakan manual

Kecocokan kanal dan durasi singkat saja belum membuktikan format Shorts maupun pengumuman awal karakter. Periksa halaman Short, konteks konten, serta sumber pengumuman pertama lintas platform. Catat URL dan timestamp pengumuman awal terpisah dari video_published_at_utc. Jangan mengisi initial_announcement_at_utc dengan timestamp Short tanpa bukti bahwa keduanya sama.

Salin registry kerja ke dalam paket bukti yang sama bila mengisinya dengan API Data. Isi channel_id dan video_published_at_utc persis dari respons API; nama karakter dapat mengikuti judul dengan catatan sumber. Pertahankan inclusion_status=pending sampai bukti manual lengkap. Gunakan verified_initial_drip_short dan included hanya setelah verifikasi tersebut; teaser/demo dikecualikan dengan alasan.

Hasil empiris tersimpan lokal di data/, tidak dimasukkan ke Git. Setelah bukti dilengkapi, jalankan audit dengan --events menunjuk registry dalam paket. Pengumpulan komentar dan analisis sentimen baru dibangun setelah audit manual dan penilaian kelayakan selesai.

Contoh menyiapkan registry di dalam paket bukti pertama: `Copy-Item data/events.csv data/metadata_candidate_001/events.csv` (hanya jika tujuan belum ada). Isi registry tersebut dengan bukti kandidat lain selama seluruh isi mengikuti waktu kedaluwarsa paket yang sama; penambahan baris tidak memperpanjang retensi. Jangan menimpa registry yang sudah diisi. Metadata hanya membuktikan status saat diambil; verifikasi ulang bila sudah kedaluwarsa.
