# Panduan pengguna — verifikasi kandidat Short

Produk tahap ini adalah CLI untuk mencatat kandidat, membaca metadata YouTube, mengisi keputusan manual, lalu mengaudit registry. Periode publikasi kandidat: Januari–September 2026, UTC. Pengumpulan komentar dan analisis sentimen dikembangkan setelah tahap ini selesai.

## 1. Unduh dan buka folder yang benar

Buka [branch proyek](https://github.com/TerKeterKeter/genshin-sentiment-research/tree/feat/offline-research-foundation). Pilih Code → Download ZIP, ekstrak, lalu buka PowerShell di folder yang berisi README.md, requirements.txt, config.json dan folder genshin_research. Folder Downloads terkadang memiliki dua lapis nama folder setelah ekstraksi.

Sebelum mengganti versi lama, salin cadangan data/ dan konfigurasi privat ke tempat lokal yang aman. Jangan mengganti berkas kerja dengan template kosong. Saat membagikan proyek ke teman, bagikan tautan GitHub; key dan data nyata tetap privat.

## 2. Instalasi dan tes offline

Python 3.12 disarankan. Jalankan dari root proyek:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m genshin_research prepare-audit
.\.venv\Scripts\python.exe -m genshin_research audit
```

Perintah di atas memakai Python virtual environment secara langsung; aktivasi PowerShell tidak diperlukan. Hasil tes harus OK. prepare-audit membuat data/events.csv dan data/discovery_coverage.csv, atau melaporkan preserved jika keduanya sudah ada. Satu kandidat contoh dari template masih pending; included_verified_events=0 dan issues=[] merupakan hasil awal yang wajar. Tes ini tidak mengakses API dan tidak memakai kuota.

Untuk macOS/Linux: buat .venv dengan python3 -m venv .venv dan ganti setiap `.\.venv\Scripts\python.exe` dengan `.venv/bin/python`.

## 3. Input link kandidat

```powershell
.\.venv\Scripts\python.exe -m genshin_research register "https://youtube.com/shorts/-2um93gmb3A" --character "Linnea"
```

Ganti link dan nama karakter untuk kandidat lain. --character opsional; nilainya adalah input peneliti, bukan konfirmasi API. Video ID dan URL diisi dari tautan; ID event dibuat otomatis dan statusnya pending. Timestamp, channel ID dan keputusan konten tidak diisi otomatis.

Karena template sudah memuat link contoh, perintah contoh biasanya menghasilkan already_registered. Ini bukan error; baris lama tidak diubah, termasuk jika sudah memiliki keputusan manual. Link baru menghasilkan registered dan menambah satu baris. Link /watch, domain lain atau ID tidak valid ditolak.

Registrasi tidak membutuhkan API key. Untuk registry selain default, tambahkan `--events data/NAMA_PAKET/events.csv` ke register. Lokasi harus berada di dalam data/.

## 4. API key ditaruh di mana?

Program membaca **environment variable YOUTUBE_API_KEY pada komputer yang menjalankannya**. Key yang disimpan di cloud tidak otomatis tersedia di laptop teman. Gunakan key proyek yang diizinkan untuk pengujian dan pastikan YouTube Data API v3 aktif di Google Cloud Console.

Di PowerShell, masukkan key lewat prompt tersembunyi berikut:

```powershell
$youtubeKey = Read-Host "Masukkan YouTube API key" -AsSecureString
$env:YOUTUBE_API_KEY = [System.Net.NetworkCredential]::new("", $youtubeKey).Password
Remove-Variable youtubeKey
```

Ketik/paste key saat prompt muncul. Nilai key tidak ditulis di perintah, history terminal atau file proyek. Jangan mengirim key/screenshot nilainya ke teman melalui laporan tes. Variabel berlaku untuk sesi PowerShell ini dan proses Python yang dijalankannya; ulangi saat membuka terminal baru. Untuk menghapusnya setelah selesai: `Remove-Item Env:YOUTUBE_API_KEY`.

Jangan menaruh key di config.json, permissions.json atau CSV. `.env.example` hanya menjelaskan nama variabel; file .env **tidak dimuat otomatis** oleh aplikasi. Jika memakai cloud, isi secret YOUTUBE_API_KEY pada pengaturan environment, simpan/publish sesuai UI, lalu jalankan di cloud tersebut.

## 5. Aktifkan scope metadata lokal

Baca [catatan kebijakan](policy-review.md). Konfigurasi di Git tetap offline/dry-run. Untuk pembacaan metadata yang kamu putuskan untuk lakukan, buat dua berkas privat memakai editor teks, misalnya VS Code. Jika berkas sudah ada, tinjau/edit isinya; jangan menimpanya tanpa cadangan.

**config.local.json**:

```json
{
  "candidate_start": "2026-01-01",
  "candidate_end_exclusive": "2026-10-01",
  "dry_run": false
}
```

**permissions.local.json**:

```json
{
  "policy_review_status": "documented",
  "policy_reviewed_at": "YYYY-MM-DD",
  "evidence_reference": "Read-only metadata audit; docs/USER_GUIDE.md and docs/policy-review.md",
  "metadata_allowed": true,
  "retention_days": 30
}
```

Ganti YYYY-MM-DD dengan tanggal kamu meninjau penggunaan metadata. JSON memakai tanda kutip ganda dan boolean true/false tanpa kutip. Simpan sebagai .json, bukan .json.txt. Kedua berkas tidak berisi key dan sudah dikecualikan Git. Scope ini hanya untuk pembacaan metadata; bukan persetujuan analisis sentimen.

## 6. Ambil metadata kandidat

Contoh untuk kandidat pertama:

```powershell
.\.venv\Scripts\python.exe -m genshin_research --config config.local.json --permissions permissions.local.json metadata --package data/metadata_candidate_001 -- -2um93gmb3A
```

Opsi global --config dan --permissions diletakkan sebelum metadata. `--` sebelum ID diperlukan karena ID contoh dimulai dengan minus. Perintah metadata menerima **ID**, sedangkan register menerima **link atau ID**.

Hasilnya berisi title, channel_id, video_published_at_utc, duration dan matches_official_channel. True pada kecocokan kanal berarti channel ID cocok dengan @GenshinImpact; hal itu tidak membuktikan klasifikasi drip marketing atau bahwa video tersebut adalah pengumuman pertama.

Bukti disimpan di data/metadata_candidate_001/metadata.json dan manifest.json. Nama paket harus baru; jika sudah ada, gunakan nama lain seperti data/metadata_candidate_001_recheck. Jangan menghapus bukti atau registry yang sudah diisi hanya untuk menjalankan ulang perintah. Setiap panggilan metadata mengambil data terbaru dan menggunakan kuota API.

## 7. Isi verifikasi manual

Siapkan registry di dalam paket bukti pertama supaya ikut aturan retensi. Perintah PowerShell berikut mempertahankan berkas tujuan jika sudah ada:

```powershell
if (!(Test-Path "data/metadata_candidate_001/events.csv")) {
    Copy-Item "data/events.csv" "data/metadata_candidate_001/events.csv"
}
```

Mulai saat ini, gunakan `data/metadata_candidate_001/events.csv` sebagai registry utama. Untuk kandidat berikutnya, register dengan --events menunjuk registry ini, lalu ambil metadata ke paket bukti baru. Jangan kembali mengisi salinan lama data/events.csv. Seluruh isi registry utama tetap mengikuti tanggal kedaluwarsa paket pertama; tambahan baris tidak memperpanjang retensi. Jika paket pertama kedaluwarsa, lakukan refresh yang sesuai dan salin ulang hanya data yang telah diperiksa/di-refresh; jangan memperpanjang manifest lama secara manual.

Buka CSV memakai editor tabel atau Excel. Pada Excel, gunakan Data → From Text/CSV, delimiter koma, encoding UTF-8, dan tipe kolom teks untuk ID/timestamp. Simpan sebagai **CSV UTF-8**, bukan .xlsx atau CSV pemisah titik koma. Program menerima UTF-8 biasa dan UTF-8 dengan BOM. Pertahankan nama kolom. Tutup CSV di Excel sebelum menjalankan perintah yang menulis file.

Tonton Short, periksa kanal resminya, dan cari bukti pengumuman awal karakter lintas platform. Isi satu baris per event:

| Kolom | Cara mengisi |
|---|---|
| event_id | Dibuat register; pertahankan ID unik ini |
| character_name | Nama karakter setelah diperiksa; boleh koreksi input awal |
| video_id, video_url | Identitas video dari register; cocokkan dengan bukti API |
| channel_id | Salin persis dari metadata.json; pastikan matches_official_channel=true |
| video_published_at_utc | Salin persis timestamp API, bukan perkiraan dari judul/pencarian |
| announcement_source_url | URL bukti pengumuman awal lintas platform |
| initial_announcement_at_utc | Waktu pengumuman awal dari bukti tersebut, dikonversi ke UTC |
| content_type | verified_initial_drip_short hanya setelah verifikasi konten selesai |
| inclusion_status | pending, included, excluded, atau no_matching_short |
| exclusion_reason | Wajib untuk excluded/no_matching_short; jelaskan alasan konkret |
| verification_notes | Bukti apa yang diperiksa, alasan keputusan, nama/inisial pemeriksa dan tanggal pemeriksaan bila sesuai prosedur tim |

Timestamp UTC menggunakan pola YYYY-MM-DDTHH:MM:SSZ. Jangan menyamakan waktu pengumuman awal dengan waktu publikasi Short tanpa bukti. Jika waktunya belum dapat dibuktikan, biarkan kosong dan pertahankan pending.

Gunakan included setelah seluruh bukti lengkap. Gunakan excluded untuk teaser/demo, video bukan kanal resmi, atau kandidat di luar periode, dengan alasan. Gunakan no_matching_short jika pencarian pengumuman telah dilakukan tetapi Short yang sesuai tidak ditemukan; status ini dapat ditambahkan manual sebagai event tersendiri walau video_id/video_url kosong. Jangan mengisi video pengganti yang tidak memenuhi definisi.

Di data/discovery_coverage.csv, catat hasil penelusuran tiap bulan: not_started, partial, atau completed. Completed berarti pencarian bulan itu telah dilakukan sesuai prosedur pencarian yang dicatat; bukan sekadar satu video ditemukan. Lengkapi checked_at_utc dan evidence_notes.

## 8. Audit hasil pengisian

```powershell
.\.venv\Scripts\python.exe -m genshin_research audit --events data/metadata_candidate_001/events.csv --coverage data/discovery_coverage.csv
```

- candidate_events: jumlah baris kandidat.
- included_verified_events: jumlah baris included yang lolos pemeriksaan kelengkapan dan periode.
- pending_events: kandidat yang masih perlu diperiksa.
- issues: masalah yang perlu diperbaiki, seperti timestamp tidak valid, bukti belum lengkap, atau ID duplikat.
- discovery_by_month: status pencarian bulan; not_started tidak berarti tidak ada event.

`issues=[]` hanya menunjukkan tidak ada masalah yang dideteksi validator, bukan bukti semua kandidat sudah terverifikasi. Data di luar periode juga dilaporkan meskipun keputusan pengecualian sudah dicatat, agar tidak masuk ringkasan event yang diterima. Hasil audit tidak otomatis mengubah keputusan manual. Kelayakan penelitian masih perlu dinilai setelah registry lengkap.

## 9. Penyimpanan dan penyerahan hasil tes

Paket berisi metadata dan registry mengikuti manifest, maksimum 30 hari. Periksa expires_at dan gunakan purge bila perlu:

```powershell
.\.venv\Scripts\python.exe -m genshin_research purge --package data/metadata_candidate_001
```

Purge biasa menghapus hanya paket yang kedaluwarsa. --force menghapus segera **seluruh isi paket**, termasuk registry; gunakan hanya jika memang hendak menghapusnya. Salinan ekspor/cadangan juga harus mengikuti aturan penyimpanan; purge tidak menemukan salinan di lokasi lain otomatis.

Gunakan [checklist pengujian](TESTING.md) untuk teman yang mencoba. Untuk laporan awal, cukup kirim versi Python, hash commit/branch, perintah yang dicoba, status berhasil/gagal, dan error yang telah diperiksa agar tidak berisi key atau data terbatas. Jangan unggah data/, config.local.json, permissions.local.json, key, atau bukti API ke Git.

## Masalah umum

| Gejala | Yang perlu diperiksa |
|---|---|
| No module named genshin_research | Terminal harus berada di folder berisi genshin_research dan config.json |
| Python tidak ditemukan | Instal Python, lalu buka ulang PowerShell; periksa python --version |
| No module named requests | Jalankan pip install lewat Python .venv seperti langkah instalasi |
| YOUTUBE_API_KEY required | Key harus tersedia pada sesi/mesin tempat Python dijalankan; secret cloud tidak tersalin ke laptop |
| Real-data operation disabled in dry-run mode | Gunakan opsi global --config config.local.json sebelum metadata |
| Document metadata access... | Periksa isi permissions.local.json, scope, tanggal, referensi dan retensi 1–30 hari |
| FileExistsError saat metadata | Paket sudah ada; gunakan nama baru dan pertahankan registry yang telah diisi |
| PermissionError saat register | Tutup CSV di Excel, lalu periksa izin tulis folder |
| Header CSV tidak lengkap | Gunakan UTF-8 dengan delimiter koma, pertahankan nama kolom; jangan ganti berkas dengan .xlsx |
| HTTP 400/403 | Periksa key, aktivasi YouTube Data API v3, kuota dan pembatasan key proyek; jangan menyalin key ke laporan |
| Transport failure | Periksa koneksi internet/proxy; untuk cloud pastikan www.googleapis.com diizinkan |
| Video unavailable or invalid ID | Periksa ID, akses video, dan apakah video masih tersedia |
