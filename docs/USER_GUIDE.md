# Panduan aplikasi untuk peneliti dan teman penguji

Semua pekerjaan sehari-hari dilakukan lewat browser. Terminal hanya untuk instalasi dan menyalakan server.

Baru pertama mencoba? Ikuti [panduan langkah demi langkah untuk teman](PANDUAN_TEMAN.md), termasuk penjelasan pesan pengaturan pada screenshot. Panduan ringkas juga tersedia pada menu **Panduan untuk teman** di aplikasi.

## 1. Instalasi

1. Unduh [branch proyek](https://github.com/TerKeterKeter/genshin-sentiment-research/tree/feat/offline-research-foundation) melalui Code → Download ZIP. Ekstrak ke folder lokal. Jika mengganti versi lama, simpan cadangan data/ dan konfigurasi privat dengan mengikuti retensinya.
2. Instal Python 3.12, buka terminal pada folder yang memiliki README.md, setup_project.py dan run.py.
3. Jalankan `python setup_project.py`. Installer membuat .venv, memasang PyTorch CPU dari indeks resmi, lalu dependensi aplikasi. Jika instalasi gagal, perbaiki koneksi/versi Python sesuai error dan ulangi; jangan menonaktifkan verifikasi TLS.
4. Jalankan `python run.py` atau klik ganda run.bat pada Windows. Buka `http://127.0.0.1:5000` di browser komputer yang sama. Jangan tutup terminal selama proses berjalan. Ctrl+C menghentikan server.

Jika port dipakai program lain: `python run.py --port 5001`, lalu buka port 5001 di browser. Python setup_project.py juga dapat dijalankan ulang untuk melengkapi instalasi. Tidak menghapus data penelitian. macOS/Linux memakai python3 jika perintah python tidak tersedia.

Instalasi dan model memerlukan ruang disk beberapa GB. Model sekitar 500 MB diunduh saat NLP pertama; proses sesudahnya memakai cache lokal. Tidak perlu GPU.

## 2. Di mana API key diisi?

Buka **Pengaturan & API**, masukkan key pada kolom password, lalu klik Simpan pengaturan. Key tidak ditampilkan kembali dan hanya disimpan di memori proses server. Setelah server ditutup, masukkan lagi saat diperlukan. Jangan mengetik key ke CSV, konfigurasi yang dilacak Git, chat atau laporan pengujian.

Alternatif untuk environment cloud: inject secret bernama YOUTUBE_API_KEY. Key cloud tidak otomatis tersedia di laptop teman. `.env.example` hanya menjelaskan nama variabel; file .env tidak dimuat otomatis. Tombol Hapus key menghapus key dari memori aplikasi.

Key proyek harus dapat memakai YouTube Data API v3. Jika mendapat HTTP 400/403, periksa aktivasi API, kuota dan pembatasan key; jangan kirim nilainya saat meminta bantuan.

## 3. Mode offline dan scope

Default **Offline / dry-run** aktif. Kamu tetap dapat mengelola kandidat dan data manual. Untuk operasi nyata, tinjau [kebijakan](policy-review.md), catat tanggal serta referensi dasar penggunaan proyek pada Pengaturan, lalu aktifkan scope yang berlaku dan nonaktifkan dry-run:

- Baca metadata: hanya videos.list/channels.list.
- Kumpulkan komentar: mengambil komentar utama untuk event yang telah diverifikasi.
- Analisis sentimen: pemrosesan dan evaluasi API Data nyata.
- Gabung revenue: agregasi sentimen dengan seri revenue eksternal.

Aktifkan secara terpisah. Checkbox mencatat scope penggunaan yang didokumentasikan, bukan pemberian izin dari platform. API key, status akademik, atau jawaban chatbot tidak otomatis menjadi dasar seluruh penggunaan turunan. Kode lengkap tetap dapat diuji dengan fixture sintetis tanpa pengumpulan data nyata.

**Masa simpan data / retensi (hari)** adalah batas penyimpanan paket, bukan jendela komentar. Misalnya 30 berarti paket disimpan paling lama 30 hari sejak dibuat, sedangkan jendela komentar tetap 72 jam. Memperpendek retensi juga memperpendek batas data yang ada; menggantinya ke angka lebih besar tidak memperpanjang expiry lama.

Jika muncul **Pengaturan penggunaan data belum lengkap**, baca butir pada halaman error, klik **Buka Pengaturan & API**, lengkapi bagian yang berlaku, lalu **Simpan pengaturan** dan ulangi langkahnya. Versi lama menampilkan pesan gabungan `Document the requested data-use scope and policy review; packages require retention of 1-30 days`; pesan itu tidak menentukan kolom mana yang salah. Tanggal tinjauan adalah tanggal pemeriksaan ketentuan oleh peneliti, dan referensi berisi sumber/rujukan serta cakupan penggunaan yang benar-benar ditinjau. Jangan mengarang persetujuan untuk mengisi form.

## 4. CRUD kandidat lewat browser

Buka **Kandidat & verifikasi**:

- **Tambah:** isi satu link `https://youtube.com/shorts/VIDEO_ID`, nama karakter opsional, klik Tambah. Duplikat ditolak tanpa membuat baris baru. Tidak ada impor massal link.
- **Baca:** daftar memperlihatkan status manual dan metadata yang tersedia. Buka / edit untuk detail.
- **Edit:** ubah nama, sumber pengumuman awal, timestamp dan catatan manusia. Perubahan link video membatalkan metadata dan mengembalikan status pending agar tidak memakai bukti video lama.
- **Hapus:** harus mencentang konfirmasi. Dataset komentar dan semua turunannya yang bergantung pada event itu juga dihapus, bukan hanya baris registry.

Untuk mencatat pengumuman tanpa Short yang sesuai, isi nama karakter dan biarkan link kosong. Lengkapi alasan penelusuran dan pilih no_matching_short. Jangan mengisi teaser/demo sebagai pengganti.

## 5. Ambil metadata dan verifikasi manual

Pada detail event klik **Ambil / refresh metadata**. Setelah proses selesai, kembali ke detail. API mengisi judul, channel ID, timestamp publikasi dan kecocokan kanal resmi. Tanggal publikasi tidak diambil dari percakapan, judul atau hasil pencarian.

Manusia tetap harus menonton Short serta memeriksa pengumuman awal lintas platform:

| Field | Sumber/pengisian |
|---|---|
| Link Short dan video ID | Input kandidat; API memverifikasi ketersediaan |
| Judul, channel ID, publikasi UTC | Respons API; tidak diedit sebagai tanggal manual |
| Nama karakter | Diperiksa peneliti berdasarkan konten |
| Sumber pengumuman awal | URL bukti pertama lintas platform |
| Waktu pengumuman awal UTC | Waktu dari bukti tersebut, terpisah dari publikasi Short |
| Jenis konten | Pilih Short pengumuman awal, sudah diperiksa hanya bila benar |
| Status | pending / included / excluded / no_matching_short |
| Alasan pengecualian | Wajib untuk excluded atau no_matching_short |
| Catatan | Bukti yang diperiksa, pemeriksa/tanggal dan alasan keputusan |

Timestamp menggunakan YYYY-MM-DDTHH:MM:SSZ atau ISO dengan timezone yang jelas. Jangan menyamakan kedua timestamp tanpa bukti. Kandidat included membutuhkan metadata resmi dan seluruh bukti manual lengkap; ketidakpastian tetap pending. Periode publikasi kandidat adalah 1 Januari hingga sebelum 1 Oktober 2026 UTC. Teaser/demo dikecualikan.

Pada **Cakupan bulanan**, catat pencarian Januari–September: not_started, partial, completed. Completed membutuhkan timestamp dan catatan strategi/bukti pencarian. Satu event ditemukan tidak membuktikan seluruh bulan telah ditelusuri.

## 6. Kumpulkan komentar

Buka **Komentar & NLP** setelah event included tersedia. Pilih:

- **Pilot temporal:** 6–8 event dipilih merata menurut waktu, bukan dugaan sentimen/revenue.
- **Semua included:** seluruh event yang memenuhi syarat; dapat dipakai untuk uji satu event, tetapi uji kecil belum membuktikan dataset layak.

Klik Mulai pengumpulan. Progress halaman dan jumlah komentar tampil pada halaman proses. API mengecek ulang metadata, kemudian menelusuri seluruh halaman commentThreads.list. Balasan/profil penulis tidak dikumpulkan. Komentar disaring lokal pada `[publikasi, publikasi+72 jam)`. Komentar editedAt pada/selepas cutoff dikeluarkan untuk analisis utama; jumlahnya dilaporkan. Likes saat pengambilan tidak menjadi bobot historis.

Setiap pengambilan membuat dataset baru. Jika jaringan, kuota atau komentar dinonaktifkan menyebabkan pengambilan terputus, hasil parsial tetap tersimpan dengan status belum lengkap. Perbaiki penyebab, lalu buat pengambilan baru; tidak ada klaim melanjutkan pagination lama secara otomatis. Dataset terputus tidak boleh masuk NLP/analisis utama. Hapus paket lama sesuai kebutuhan dan retensi.

Jangan menghentikan server saat proses berjalan. Satu pekerjaan dijalankan pada satu waktu. Jika server ditutup, pekerjaan berhenti dan status lengkap tidak dipaksakan.

## 7. NLP sentimen lokal

Buka dataset lengkap, klik **1. Jalankan NLP lokal**. Unduhan pertama memerlukan internet ke Hugging Face dan CDN bobotnya. Model memakai revision tetap dan checksum; jika unduhan gagal, perbaiki jaringan/cache yang bermasalah dan ulangi, bukan mengubah checksum atau mematikan TLS.

Teks dinormalisasi whitespace/NFC tanpa menghapus negasi/emoji. Bahasa dideteksi dengan seed tetap; komentar non-Inggris/undetermined dikeluarkan dan jumlahnya dilaporkan. Spam dan teks identik ditandai, tidak otomatis dihapus. Bahasa pendek/slang dapat salah terdeteksi. Input panjang yang dipotong ke 512 token diberi penanda.

Model mengembalikan positive/negative/neutral. Label adalah prediksi, bukan ground truth. Komentar tidak dikirim ke API AI eksternal. Model dilatih pada Twitter sehingga evaluasi manual untuk YouTube tetap penting.

## 8. Anotasi dan evaluasi

Klik **2. Anotasi manual**, lalu Buat sampel. Maksimum 200 komentar dipilih acak berstrata event × interval 0–24/24–48/48–72 jam, seed 42. Jika eligible kurang, semua tersedia dipakai; laporkan jumlah sebenarnya.

Prediksi model disembunyikan. Isi label sesuai panduan pada halaman; anotator 1/2 bekerja independen. Positive = evaluasi menyukai; negative = ketidaksukaan/kritik; neutral = tanpa evaluasi jelas. Niat gacha tidak otomatis positif. Tandai ambiguous/off_topic terpisah. Jika belum dapat diputuskan, kosongkan gold; isi adjudicated_label setelah adjudikasi.

Simpan setiap halaman sebelum berpindah. CSV sampel dapat diunduh dan diisi privat oleh anotator, lalu diimpor kembali; gunakan ID sampel yang sama. Teks dan identitas sampel tidak diganti oleh upload. Ikuti retensi untuk salinan yang dibagikan.

Klik **3. Evaluasi model**. Hasil: jumlah gold yang benar-benar digunakan, macro-F1, confusion matrix, jumlah belum dinilai, dan Cohen κ jika tersedia dua set label yang memadai. Skor tidak muncul bila gold kosong. Tidak ada ambang skor yang secara otomatis menjamin penelitian layak. Perubahan anotasi/NLP membatalkan hasil evaluasi/analisis lama.

## 9. Revenue manual

Buka **Revenue**. Unduh template CSV atau isi satu bulan lewat form. Gunakan **satu seri** dengan cakupan mobile, wilayah dan CN Android konsisten. Kandidat sumber https://revenue.ennead.cc/revenue harus diperiksa manual; aplikasi tidak mengarang angka.

- month: YYYY-MM, tepat satu revisi yang dipilih per bulan.
- revenue_usd: angka USD tanpa pemisah ribuan; kosong = hilang, 0 = nilai nol. Konversikan satuan juta jika sumber memakai juta USD dan dokumentasikan.
- platform_scope / region_scope: cakupan eksplisit sumber.
- cn_android_included: true/false/unknown; multiplier positif hanya bila komponen tersebut disertakan dan estimasinya relevan. Jelaskan komponen/revisi di revision_notes.
- source_url: URL seri sumber HTTPS tanpa kredensial.
- retrieved_at: tanggal pengambilan atau timestamp ISO dengan timezone.
- available_at_utc: waktu nilai/revisi tersebut benar-benar tersedia dari sumber. Opsional untuk korelasi, wajib untuk eksperimen forecast; jangan isi tanggal historis dari perkiraan atau menyamakan retrieval sekarang dengan ketersediaan masa lalu.

Impor CSV meminta konfirmasi karena mengganti seri yang ada. Perubahan seri membatalkan hasil analisis lama. Duplikasi bulan, angka nonfinite/negatif dan cakupan campuran ditolak. Validasi format tidak membuktikan kebenaran angka maupun hak penggunaan sumber.

## 10. Analisis hubungan bulanan

Setelah NLP dan evaluasi manual, klik **4. Analisis revenue t+1**. Semua event/komentar berasal dari snapshot dataset yang sama; registry yang berubah sesudah koleksi ditandai agar tidak tercampur diam-diam.

Komentar eligible digabung menurut bulan saat jendela 72 jam berakhir. Hasil berisi jumlah event/komentar, proporsi tiga kelas, dan net sentiment = positive proportion − negative proportion. Event dengan banyak komentar mempunyai kontribusi lebih besar; likes tidak dibobotkan. Bulan tanpa event tidak diisi netral, dan bulan dengan event tetapi tanpa komentar eligible memiliki net sentiment kosong.

Agregat bulan t dipasangkan dengan revenue t+1 hanya jika bulan revenue sudah selesai dan nilainya tersedia. Jumlah pasangan aktual dan alasan tidak berpasangan dilaporkan. Scatter berlabel bulan dan Spearman dibuat bila data bervariasi dan jumlah pasangan memadai untuk dihitung (minimum teknis 3, bukan jaminan power statistik). Revenue tidak digandakan ke setiap komentar.

Berkas monthly.csv, pairs.csv, coverage.csv, revenue.csv snapshot, analysis.json, dan scatter.png dapat diunduh. Jangan menafsirkan hubungan sebagai kausal. Perhatikan tren, update, rerun, serial dependence dan beda audiens/revenue.

## 11. Forecasting eksperimen

Klik **5. Forecast eksperimen** setelah analisis. Ridge dengan satu fitur net sentiment dibandingkan naïf revenue terakhir. Scaling hanya fit pada training; evaluasi berurutan waktu, bukan random split. Target training hanya digunakan jika waktu ketersediaannya sebelum origin evaluasi.

Pemeriksaan: minimal 8 pasangan berurutan tanpa gap, variasi fitur, scope penelusuran selesai tanpa pending, tanggal ketersediaan revenue terdokumentasi, dan setidaknya 3 origin evaluasi dengan minimal 4 training points. Ini ambang teknis demonstrasi, bukan jaminan kelayakan ilmiah. Dataset sembilan bulan dapat gagal memenuhi pemeriksaan.

Hasil dapat berupa blocked, hindcast_only, atau experimental_projection. Hindcast memakai komentar yang direkonstruksi retrospektif; bukan arsip komentar lengkap pada waktu historis dan bukan bukti akurasi real-time. MAE Ridge dan baseline dilaporkan, termasuk bila model tidak mengalahkan baseline.

Estimasi untuk target bulan berjalan diberi label nowcast, bukan prediksi masa depan. Target yang sudah diketahui/berlalu tidak diberi label future forecast. Tidak ada proyeksi per karakter atau interval kepercayaan palsu. Jangan gunakan eksperimen ini sebagai saran finansial atau klaim sebab-akibat.

## 12. Data, penghapusan dan pengujian teman

Aplikasi memakai data/workbench. Saat inisialisasi pertama, registry/coverage lama data/events.csv dan data/discovery_coverage.csv disalin jika ada; sumber asli tetap utuh. Setelah itu gunakan browser agar tidak mengedit salinan berbeda. Ekspor CSV tersedia untuk inspeksi.

Key browser hilang saat proses server berhenti. CSV/JSON data tetap tersimpan. Metadata mempunyai expiry per event; pada expiry metadata dikosongkan dan included kembali pending. Dataset mempunyai manifest maksimum 30 hari yang mencakup komentar, prediksi, anotasi dan semua turunan. Paket kedaluwarsa dihapus ketika aplikasi aktif dan tidak ada job berjalan; jalankan aplikasi secara berkala atau lakukan penghapusan terjadwal sendiri jika tidak aktif.

Menghapus event menghapus pula dataset/turunan yang merujuknya. Menghapus dataset menghapus seluruh isi paketnya. Konfirmasi diperlukan. Cadangan dan ekspor di luar folder aplikasi tidak ditemukan purge otomatis; ikuti retensi secara terpisah.

Aplikasi diikat ke localhost untuk satu pengguna lokal, bukan deployment multiuser. Teman menjalankan salinan sendiri di komputernya. Jangan masukkan data nyata/key ke Git atau mengirimnya dalam laporan tes. Gunakan [checklist penguji](TESTING.md).

### Masalah umum

| Gejala | Tindakan |
|---|---|
| No module named pip | Installer terbaru memulihkan pip otomatis. Untuk versi lama: `.\.venv\Scripts\python.exe -m ensurepip --upgrade`, lalu ulangi setup |
| No module named flask / instalasi belum lengkap | Setup belum berhasil sampai akhir. Jalankan python setup_project.py sampai muncul Instalasi selesai, baru python run.py |
| Modul/dependensi lain tidak ditemukan | Jalankan ulang python setup_project.py dari folder proyek |
| Browser tidak tersambung | Pastikan python run.py tetap berjalan; periksa port pada terminal |
| Operasi diblokir offline/scope | Periksa Pengaturan: dry-run, scope yang berlaku, tanggal dan referensi dasar penggunaan |
| Key belum tersedia/HTTP 400/403 | Isi key di browser; periksa aktivasi API, kuota dan restriction proyek |
| Pengambilan terputus | Perbaiki error, lalu buat dataset baru; jangan menjadikan data parsial sebagai lengkap |
| NLP model tidak dapat diunduh | Periksa ruang disk, koneksi HTTPS huggingface.co dan CDN, khususnya us.aws.cdn.hf.co |
| Tidak ada eligible Inggris | Periksa eksklusi waktu/edit/bahasa, serta sampel deteksi bahasa; jangan memaksa label |
| Gold manual kosong | Buat sampel, isi/adjudikasi label, simpan halaman, lalu evaluasi |
| Forecast blocked | Baca alasan kecukupan/ketersediaan data; jangan mengarang bulan atau angka agar lolos |

Pada cloud dengan allowlist jaringan, model card dan bobot bisa memakai domain berbeda. Draft domain CDN yang disimpan belum otomatis mengubah runtime; tinjau/simpan dan publish pengaturan environment. Semua instalasi tetap mempertahankan verifikasi TLS dan checksum.
