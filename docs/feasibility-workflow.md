# Fase 2: audit kelayakan, sebelum pengumpulan komentar

## Berkas kerja lokal

Salin template ke area yang diabaikan Git; perintah berikut menolak menimpa berkas yang sudah ada:

```python
from pathlib import Path
for filename in ['events.csv', 'discovery_coverage.csv', 'revenue.csv']:
    destination = Path('data') / filename
    destination.parent.mkdir(exist_ok=True)
    with destination.open('x', encoding='utf-8', newline='') as stream:
        stream.write((Path('templates') / filename).read_text(encoding='utf-8'))
```

Registry berisi satu tautan kandidat, bukan hasil terverifikasi. Jangan menetapkan tanggal publikasinya sebelum API mengonfirmasi. Simpan hasil penelusuran per bulan Januari–September 2026 di discovery_coverage.csv: not_started, partial, completed. `completed` membutuhkan waktu pemeriksaan dan catatan bukti/strategi pencarian yang memungkinkan audit ulang. Tidak ditemukannya event dalam registry kosong bukan bukti tidak ada event.

## Audit kalender tanpa API

```bash
python -m genshin_research audit --events data/events.csv --revenue data/revenue.csv --coverage data/discovery_coverage.csv --as-of 2026-10-25
```

Gunakan tanggal audit aktual saat mengulang; `--as-of` membuat laporan dapat direproduksi. Laporan memisahkan sebaran publikasi dan akhir jendela, penelusuran yang belum dilakukan, revenue yang belum diimpor, serta bulan revenue yang belum selesai. Jumlah pasangan **potensial** membutuhkan event terverifikasi dan revenue; pasangan **aktual** baru dihitung setelah komentar eligible dan sentimen tervalidasi tersedia.

Periode kandidat mengikuti tanggal publikasi Short. Akhir jendela 72 jam untuk Short akhir September dapat masuk Oktober; target revenue menjadi November. Pada 25 Oktober 2026, bulan revenue Oktober dan November belum lengkap. Tanpa menunggu rilis data bulan tersebut, event tertentu tidak dapat dipasangkan. Jangan memasukkan estimasi sementara sebagai bulan penuh tanpa perubahan protokol.

## Bukti event dan revenue

Untuk setiap kandidat, catat tautan pengumuman pertama lintas platform dan timestamp-nya secara terpisah dari metadata Short. Periksa channel ID resmi melalui API, bukti format Short, dan kecocokan sebagai pengumuman awal karakter. Teaser/demo tetap dikecualikan. Bila tidak ada Short yang sesuai gunakan no_matching_short disertai catatan penelusuran; jangan mengisi karakter/event yang belum terbukti.

Untuk revenue, impor manual satu seri, sertakan cakupan platform/wilayah, status CN Android dan multiplier, sumber, tanggal akses dan revisi. Angka yang tidak tersedia tetap kosong. Jangan menyebut seri konsisten sebelum sumber diperiksa; validasi kode atas kolom tidak membuktikan provenance sebenarnya.

## Kriteria lanjut pilot

1. Use case dan kewajiban penyimpanan telah ditinjau; izin yang berlaku terdokumentasi, khususnya additional derived metrics dan penggunaan revenue eksternal.
2. API key tersedia sebagai environment variable privat, bukan file yang dilacak Git.
3. Penelusuran bulanan cukup lengkap untuk menilai cakupan; 6–10 event eligible dari periode berbeda tersedia untuk pilot (jika kurang, laporkan dan evaluasi ulang desain).
4. Revenue konsisten dan jumlah bulan yang berpotensi dipasangkan diketahui. Tiga pasangan nonkonstan hanya batas komputasi skrip, bukan jaminan kelayakan ilmiah atau power statistik.

Pengumpulan, inferensi dan korelasi data nyata belum dijalankan pada fase ini. Tidak ada forecasting.
