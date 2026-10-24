# Pengelolaan data dan izin

## Pemeriksaan wajib sebelum data nyata

Sumber resmi yang harus dibaca ulang dan dicatat tanggal/versinya:
- https://developers.google.com/youtube/terms/developer-policies
- https://developers.google.com/youtube/terms/derived-metrics-policy

Kedua halaman berhasil dibaca pada fase audit berikutnya; lihat [catatan pemeriksaan](policy-review.md). Pemilik proyek baru memiliki API key; persetujuan additional derived metrics belum ditetapkan. Jangan menganggap API key, akses teknis atau status akademik mengizinkan analisis sentimen, penyimpanan label/embedding/metrik turunan atau penggabungan revenue eksternal. Minta penilaian penanggung jawab proyek dan dokumentasikan bukti izin/pengecualian yang berlaku; boolean aplikasi bukan pemberian izin oleh YouTube.

`permissions.json` memisahkan collection_allowed, derived_analysis_allowed, external_join_allowed. Isi policy_review_status=documented, policy_reviewed_at, evidence_reference dan retention_days hanya setelah kewajiban spesifik proyek dipastikan. Untuk paket campuran yang masih berisi teks, kode menerima retensi 1–30 hari; pengecualian penyimpanan turunan lebih lama tidak diimplementasikan. Catat dasar hukum/kebijakan, cakupan data, pihak yang menyetujui, tujuan, refresh, deletion dan pembatasan ekspor. Jangan mengaktifkan operasi jika ada penggunaan yang masih belum diizinkan.

## Siklus hidup

Simpan data nyata hanya di `data/<paket>/`, dengan manifest tanggal pengambilan dan kedaluwarsa, serta status pagination. Nama, avatar dan profil penulis tidak dikumpulkan. ID komentar tetap data yang perlu dilindungi; akses lokal terbatas, enkripsi media penyimpanan bila tersedia, tanpa ekspor ke layanan AI eksternal. Jangan menaruh key dalam log/Git/notebook. `.gitignore` bukan kontrol akses.

`python -m genshin_research purge --package data/pilot_run_01` menghapus seluruh paket yang kedaluwarsa; `--force` untuk pencabutan izin, permintaan penghapusan, atau penghapusan segera. Penghapusan mencakup teks, label, anotasi, agregat dan plot dalam paket. Jalankan sebelum tiap sesi; jadwalkan secara eksternal jika lingkungan tidak selalu hidup. Salinan ekspor/backups harus masuk inventaris dan dihapus terpisah. Penyimpanan turunan bukan otomatis permanen.

Refresh metadata: `metadata --refresh -- VIDEO_ID` setelah gate izin. Refresh komentar yang masih diizinkan dilakukan dengan pengambilan ulang lengkap ke paket baru, lalu purge paket lama dan hitung ulang seluruh turunan. Jangan memperpanjang timestamp lama secara buta; tangani komentar yang hilang/berubah dan instruksi penghapusan. Perintah refresh metadata tidak menyegarkan teks komentar atau izin turunan. Jangan menyimpan komentar/derivatif di luar paket yang tercakup manifest.

## Revenue

Kandidat: https://revenue.ennead.cc/revenue (belum diambil/diverifikasi). Impor manual satu seri konsisten. Dokumentasikan platform mobile, wilayah, sumber estimasi, status CN Android, multiplier (kosong jika tidak berlaku), bulan hilang, tanggal pengambilan dan revisi. `revenue_usd` angka USD tanpa pemisah; kosong berarti hilang, bukan nol. Jangan mencampur cakupan atau memilih revisi berbeda secara diam-diam; simpan sumber dan catatan revisi. Audit potensi pasangan bukan bukti kualitas seri. Hak penggunaan sumber revenue juga perlu diperiksa.
