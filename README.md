# Genshin sentiment research

Tahap aktif: menyiapkan dan memverifikasi manual kandidat Shorts drip marketing karakter Genshin Impact, Januari–September 2026, dari kanal resmi @GenshinImpact.

API hanya membaca judul, channel ID dan waktu publikasi. Penentuan apakah video benar-benar pengumuman awal/drip marketing dilakukan manusia. Teaser/demo tidak menggantikan kandidat yang hilang.

## Instalasi

Python 3.12 disarankan. Di PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m genshin_research prepare-audit
```

Perintah terakhir membuat `data/events.csv` dan `data/discovery_coverage.csv`. Jika sudah ada, isinya dipertahankan. Berkas revenue/output dari versi lama yang berada di data lokal juga tidak dihapus.

## Langkah yang dilakukan sekarang

1. Tambahkan kandidat melalui terminal, atau isi langsung data/events.csv. Contoh:

   ```powershell
   python -m genshin_research register "https://youtube.com/shorts/-2um93gmb3A" --character "Linnea"
   ```

   Ganti link dan nama untuk kandidat lain. --character bersifat opsional dan merupakan input peneliti, bukan hasil verifikasi API. ID event dibuat otomatis; status selalu pending. Link yang sama menghasilkan already_registered tanpa mengubah keputusan atau data yang sudah ada. Registrasi berjalan offline tanpa API key dan tidak membuktikan format Shorts maupun waktu publikasi. Link diterima pada register; perintah metadata tetap menerima ID video.

2. Verifikasi metadata API sesuai [panduan metadata](docs/metadata-audit.md). Tidak ada komentar yang diambil.
3. Periksa sendiri konten Short dan sumber pengumuman awal lintas platform. Catat timestamp pengumuman awal terpisah dari timestamp publikasi Short, serta bukti dalam verification_notes.
4. Tentukan keputusan manual menggunakan tabel di bawah. Jangan mengisi tanggal atau bukti dari perkiraan.
5. Catat status penelusuran setiap bulan dalam discovery_coverage.csv: not_started, partial, atau completed. completed membutuhkan checked_at_utc dan evidence_notes. Registry kosong tidak membuktikan tidak ada event.

| Keputusan | inclusion_status | Catatan |
|---|---|---|
| Belum selesai diperiksa | pending | Biarkan kolom yang belum diketahui kosong |
| Memenuhi definisi penelitian | included | Lengkapi seluruh bukti; content_type=verified_initial_drip_short |
| Video tidak memenuhi kriteria | excluded | Isi exclusion_reason |
| Pengumuman telah dicari tetapi tidak ada Short yang sesuai | no_matching_short | Catat alasan dan bukti penelusuran |

Audit registry lokal:

```powershell
python -m genshin_research audit
```

Jika registry berisi metadata API, simpan di paket yang memiliki manifest retensi (lihat panduan), lalu tunjuk berkasnya:

```powershell
python -m genshin_research audit --events data/metadata_candidate_001/events.csv --coverage data/discovery_coverage.csv
```

Audit memeriksa kelengkapan kolom, timestamp, periode kandidat, duplikasi ID, dan sebaran event yang telah dicatat included. Audit tidak menonton video atau menyatakan keputusan manusia pasti benar. Periode berlaku pada publikasi Short: `2026-01-01 <= tanggal UTC < 2026-10-01`.

## Tes tanpa API

```powershell
python -m unittest discover -s tests -v
```

Tes memakai data sintetis dan HTTP mock. Tidak menggunakan kuota API, mengambil komentar, atau mengunduh model. Opsional: `python -m pip install -r requirements-dev.txt`, lalu `python -m ruff check genshin_research` dan `python -m ruff format --check genshin_research`.

## Yang ditunda

Pengumpulan komentar, preprocessing, inferensi sentimen, anotasi, evaluasi model, impor revenue dan analisis hubungan bulanan belum tersedia dalam versi aktif. Implementasi sebelumnya tersimpan dalam riwayat Git, misalnya commit `ee3b941`; tidak perlu dipasang untuk verifikasi manual.

Setelah audit manual dan penilaian kelayakan selesai, tahap selanjutnya dapat dibangun: komentar utama Inggris pada 72 jam pertama, sentimen positif/negatif/netral memakai model pretrained lokal tanpa fine-tuning, evaluasi manual, lalu agregasi akhir-jendela bulan t terhadap estimasi mobile revenue t+1 dari satu seri konsisten. Tidak ada forecasting pada tahap awal.

Hubungan tersebut bersifat eksploratif, bukan kausal. Komentator bukan representasi seluruh pemain/pembayar. Data retrospektif tidak merekonstruksi komentar yang telah dihapus. Tren waktu, update game, rerun banner dan beda cakupan audiens/revenue perlu dilaporkan; sembilan bulan kandidat tidak menjamin dataset cukup.

## Data dan konfigurasi

Default offline/dry-run; key dibaca dari environment YOUTUBE_API_KEY. `.env.example` hanya contoh nama variabel, tidak dimuat otomatis. Jangan masukkan key, bukti API atau data penelitian ke Git/chat. Data lokal dan konfigurasi *.local.json diabaikan Git. Secret cloud tidak otomatis tersedia di PowerShell lokal.

Lihat [panduan metadata dan retensi](docs/metadata-audit.md) serta [catatan kebijakan](docs/policy-review.md). Dokumen tersebut tetap dipertahankan untuk menjelaskan batas penggunaan data.
