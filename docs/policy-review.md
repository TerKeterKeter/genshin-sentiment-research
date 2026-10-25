# Catatan kebijakan penggunaan data

Dua halaman resmi berhasil diperiksa pada 25 Oktober 2026 (Asia/Jakarta):

- [YouTube API Services Developer Policies](https://developers.google.com/youtube/terms/developer-policies), pembaruan halaman 15 Oktober 2026. Bagian III.E.4 menjelaskan ketentuan data/metrik turunan dan penyimpanan; III.L membahas jalur kebijakan tambahan bagi use case analytics yang diterima.
- [Additional policies for derived metrics and data storage](https://developers.google.com/youtube/terms/derived-metrics-policy), pembaruan halaman 14 September 2026. Viewer Sentiment Analysis dicantumkan sebagai contoh penggunaan dalam kebijakan tambahan yang bersyarat. Bagian Data Storage tetap menerapkan refresh/penghapusan 30 hari untuk teks komentar dan metadata tertentu; allowance turunan hingga 36 bulan bukan izin penyimpanan permanen untuk semua data.

Versi aktif menyediakan kode lengkap koleksi, NLP dan analisis melalui browser, tetapi default tetap offline. Metadata, pengumpulan komentar, pemrosesan turunan dan penggabungan revenue mempunyai scope terpisah yang harus didokumentasikan di Pengaturan. Pembacaan metadata biasa dibedakan dari analisis sentimen; scope metadata_allowed tidak memberikan persetujuan untuk penggunaan turunan.

Sebelum menjalankan pengumpulan/analisis data nyata, tinjau kembali ketentuan terbaru dan dokumentasikan dasar penggunaan proyek, cakupan, retensi, serta penggabungan revenue eksternal. Klaim pengecualian akademik belum didukung rujukan resmi; jawaban chatbot tidak dipakai sebagai bukti persetujuan platform. Keberadaan kode dan checkbox scope tidak menetapkan bahwa proyek sudah mendapat persetujuan platform.

Bukti API disimpan lokal dalam paket dengan manifest dan retensi maksimum 30 hari. Gunakan penghapusan/refresh pada aplikasi sesuai [panduan pengguna](USER_GUIDE.md). Allowance penyimpanan turunan 36 bulan tidak diterapkan: seluruh dataset berisi teks dan turunannya tetap dibatasi maksimum 30 hari. Jangan menyimpan key, metadata atau data terbatas di Git.
