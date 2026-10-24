# Audit kebijakan sebelum pilot

Tanggal catatan: 25 Oktober 2026 (Asia/Jakarta). Kedua halaman resmi berhasil diakses HTTP 200 pada fase audit ini. Kegagalan 403 pada fase sebelumnya bukan lagi status akses kebijakan terkini.

## Sumber dan temuan

1. [YouTube API Services Developer Policies](https://developers.google.com/youtube/terms/developer-policies), halaman menyatakan **Last updated 2026-10-15 UTC**. Bagian III.E.4 melarang penggunaan API Data untuk membuat data/metrik turunan secara umum. Bagian III.L menjelaskan kebijakan tambahan hanya berlaku untuk audited developers dengan use case analytics yang secara eksplisit mengajukan izin melalui proses quota extension (mulai 1 Juni 2026).
2. [Additional policies for derived metrics and data storage](https://developers.google.com/youtube/terms/derived-metrics-policy), halaman menyatakan **Last updated 2026-09-14 UTC**. Pembukaan mensyaratkan penerimaan amendment dan mengarahkan pemilihan Section 5 → Analytics & Reporting. Bagian [Viewer Sentiment Analysis](https://developers.google.com/youtube/terms/derived-metrics-policy#sentiment) mencantumkan NLP komentar sebagai contoh penggunaan yang diperbolehkan **dalam cakupan kebijakan tambahan tersebut**. Ini bukan izin otomatis bagi setiap pemilik API key.
3. Bagian [Data Storage](https://developers.google.com/youtube/terms/derived-metrics-policy#data-storage) mengizinkan statistik tertentu dan derived metrics hingga 36 bulan bagi accepted API Clients. Teks komentar, judul dan deskripsi tetap tunduk pada refresh/deletion 30 hari. Ketentuan ini tidak membuat semua data turunan otomatis boleh disimpan permanen.

## Keputusan proyek saat ini

Pemilik proyek mengonfirmasi baru memiliki API key; bukti persetujuan additional derived metrics belum tersedia. API key juga belum diinjeksi ke mesin cloud. Status `reviewed_pending_project_permission`; seluruh izin operasi nyata tetap false dan dry-run tetap true. `policy_reviewed_at` mencatat pemeriksaan dokumen, bukan tanggal pemberian izin.

- Akses teknis metadata/komentar tidak sama dengan izin analisis sentimen.
- Bukti penerimaan/persetujuan yang berlaku untuk proyek harus dicatat di konfigurasi privat. Persetujuan dosen/etik kampus tidak menggantikan ketentuan platform.
- Penggabungan sentimen dengan estimasi **revenue game mobile eksternal** belum ditetapkan tercakup. Contoh Financial Performance Projections di halaman resmi membahas revenue kanal YouTube; jangan menganggapnya persetujuan otomatis untuk penelitian revenue game. Jelaskan use case lengkap saat meminta klarifikasi/persetujuan resmi.
- Sebelum pengumpulan, tentukan kewajiban privasi, refresh, permintaan penghapusan, ekspor dan retensi. Gunakan rujukan formulir resmi dari halaman kebijakan; jangan mengandalkan boolean aplikasi sebagai pemberian izin.

## Implementasi retensi yang konservatif

Paket lokal menggabungkan teks, metadata, anotasi dan agregat. Karena belum memisahkan lifecycle teks dan turunan, seluruh paket dibatasi **maksimal 30 hari**, atau lebih singkat bila diwajibkan. Kode tidak mengimplementasikan pengecualian penyimpanan turunan 36 bulan. `purge` tetap tersedia saat izin belum diberikan. Refresh komentar berarti pengambilan ulang yang diizinkan dan penghapusan paket lama beserta turunan; refresh metadata saja tidak menyegarkan teks.

## Keterbatasan akses lain

https://revenue.ennead.cc/revenue masih ditolak proxy HTTP 403. Belum ada angka atau cakupan seri yang diverifikasi. Domain tersebut perlu diizinkan di pengaturan jaringan environment, atau sumber dapat diperiksa manual oleh peneliti dan diimpor ke CSV sesuai template. Jangan mengubah sumber/cakupan secara diam-diam.
