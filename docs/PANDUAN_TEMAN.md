# Panduan teman: dari instalasi sampai mengambil komentar YouTube

Tujuan percobaan pertama: aplikasi terbuka, satu kandidat tercatat, metadata dari API muncul, verifikasi manusia tersimpan, lalu komentar berhasil diambil menjadi dataset lengkap. Setelah itu lanjutkan NLP dan evaluasi. Satu video belum cukup untuk menyimpulkan hubungan sentimen–revenue.

Setelah aplikasi berjalan, panduan singkat juga tersedia melalui menu **Panduan untuk teman**. Tidak perlu mengetik link atau data penelitian satu per satu di PowerShell.

## 1. Siapkan aplikasi di Windows

1. Instal **Python 3.12** dari https://www.python.org/downloads/windows/. Aktifkan opsi menambahkan Python ke PATH saat instalasi.
2. Unduh [ZIP branch pengembangan](https://github.com/TerKeterKeter/genshin-sentiment-research/archive/refs/heads/feat/offline-research-foundation.zip), lalu ekstrak. Branch ini memuat panduan dan perbaikan terbaru; ZIP `main` baru memuatnya setelah perubahan digabungkan.
3. Buka folder hasil ekstrak sampai terlihat `README.md`, `setup_project.py`, dan `run.py`. Pada File Explorer, klik bilah alamat folder, ketik `powershell`, lalu Enter.
4. Periksa Python dan jalankan instalasi:

```powershell
python --version
python setup_project.py
```

Tunggu sampai muncul **Instalasi selesai**. Instalasi pertama membutuhkan internet dan ruang disk beberapa GB. Tidak perlu GPU. Jika muncul error, perbaiki penyebabnya dan ulangi setup sebelum melanjutkan.

5. Jalankan server:

```powershell
python run.py
```

6. Buka **http://127.0.0.1:5000** di browser komputer yang sama. Biarkan terminal tetap terbuka. Bila port sudah digunakan, jalankan `python run.py --port 5001` dan buka alamat dengan port 5001.

Pada penggunaan berikutnya cukup `python run.py` atau klik ganda `run.bat`. Ctrl+C menghentikan server. Jangan menghentikannya saat pengambilan komentar atau NLP berjalan.

**Jika memakai versi baru:** hentikan server, cadangkan folder `data/` dengan tetap mengikuti retensi, ekstrak kode baru, dan instal dependensinya. Jika berpindah folder, gunakan salinan `data/` yang diperlukan tetapi buat `.venv` melalui setup di folder baru; jangan memindahkan `.venv` antar folder. Jangan membagikan folder data sebagai bagian ZIP untuk teman.

### Jika setup gagal seperti laporan sebelumnya

Untuk `No module named pip` pada versi lama:

```powershell
.\.venv\Scripts\python.exe -m ensurepip --upgrade
python setup_project.py
```

Installer terbaru mencoba memperbaiki pip secara otomatis. `No module named flask` biasanya akibat setup belum berhasil memasang dependensi. Ulangi `python setup_project.py` hingga selesai, baru jalankan aplikasi. Tidak perlu menghapus data atau hasil verifikasi.

## 2. Bedakan input manusia dan pengambilan otomatis

| Bagian | Cara diperoleh |
|---|---|
| Link kandidat Short dan nama karakter | Diisi manusia melalui form |
| Judul, channel ID, waktu publikasi Short, kecocokan kanal resmi | Diambil otomatis melalui API setelah tombol metadata diklik |
| Keputusan apakah benar drip marketing/pengumuman awal | Diperiksa manusia; API tidak memutuskan |
| Sumber dan waktu pengumuman awal lintas platform | Dicari dan dicatat manusia, terpisah dari publikasi Short |
| Komentar utama dan timestamp-nya | Diambil otomatis melalui API setelah tombol pengumpulan diklik |
| Kelayakan waktu, bahasa, prediksi sentimen | Diproses kode; bahasa dan sentimen tetap dapat keliru |
| Label evaluasi manusia | Diisi anotator, tidak disalin dari prediksi model |
| Revenue bulanan dan cakupan sumber | Diisi melalui form/CSV manual |

Tidak ada pencarian massal link, klasifikasi drip marketing otomatis, atau pengambilan terjadwal. Otomatis berarti aplikasi menjalankan permintaan API setelah pengguna memilih langkahnya.

## 3. Masukkan API key dan atur penggunaan data

### API key di mana?

1. Buka **Pengaturan & API** di menu kiri.
2. Pada **Masukkan key untuk sesi server ini**, tempel API key milik proyek penelitian. Gunakan key untuk **YouTube Data API v3**, bukan key layanan AI.
3. Jangan centang **Hapus key dari memori server** kecuali memang hendak menghapusnya.
4. Lengkapi pengaturan di bawah, kemudian klik **Simpan pengaturan**. Periksa bahwa status key menjadi tersedia.

Jika belum punya key, penanggung jawab proyek membuat/memilih proyek di [Google Cloud Console](https://console.cloud.google.com/), mengaktifkan **YouTube Data API v3**, lalu membuat API key pada **APIs & Services → Credentials**. Pembatasan key harus sesuai pemakaian aplikasi lokal dan hanya API yang diperlukan. Jika key sudah tersedia, tidak perlu membuat key baru.

Key dari form hanya ada di memori server. Setelah terminal/server ditutup, masukkan lagi saat diperlukan. Key di konfigurasi rahasia cloud tidak otomatis berpindah ke laptop teman. `.env` tidak dimuat otomatis oleh aplikasi. Jangan menaruh key di CSV, source code, Git, screenshot, atau pesan bantuan.

### Arti setiap pengaturan

| Isian | Maksud dan cara mengisi |
|---|---|
| **Offline / dry-run** | Jika dicentang, pengambilan dan pemrosesan data YouTube nyata diblokir. Cocok untuk input kandidat/data manual. Nonaktifkan hanya setelah dasar penggunaan langkah nyata diperiksa. |
| **Baca metadata YouTube** | Diperlukan untuk **Ambil / refresh metadata**. Aktifkan jika penggunaan ini tercakup dalam catatan proyek. |
| **Kumpulkan komentar utama** | Diperlukan untuk **Mulai pengumpulan**. Belum diperlukan jika baru memeriksa metadata. |
| **Analisis sentimen dan evaluasi data nyata** | Diperlukan untuk NLP, anotasi, dan evaluasi terhadap data nyata. |
| **Gabungkan agregat dengan revenue eksternal** | Diperlukan untuk analisis revenue dan forecast, bersama operasi analisis sentimen. |
| **Tanggal tinjauan kebijakan** | Tanggal ketika peneliti benar-benar memeriksa ketentuan dan dasar penggunaan proyek; bukan tanggal video atau tanggal data yang ingin dianalisis. |
| **Masa simpan data / retensi (hari)** | Bilangan bulat **1–30**. Misalnya `30` berarti paket disimpan paling lama 30 hari sejak dibuat. Ini bukan jendela komentar. |
| **Referensi dasar penggunaan proyek** | Catat sumber/URL atau dokumen yang benar-benar ditinjau, operasi yang dicakup, serta pembatasannya. Jangan mengarang nomor persetujuan atau menganggap teks form memberi izin. |

Untuk menulis referensi, gunakan kerangka berikut dan ganti setiap bagian dengan hasil peninjauan yang sebenarnya. Kerangka ini bukan bukti izin dan tidak perlu disalin sebagai isian jika peninjauan belum dilakukan:

```text
Sumber/URL atau dokumen yang ditinjau: [rujukan nyata]
Operasi yang dicakup: [metadata / komentar / sentimen / penggabungan eksternal]
Dasar kesesuaian penggunaan proyek: [hasil pemeriksaan atau rujukan yang relevan]
Batas penggunaan dan penyimpanan: [batas yang berlaku untuk proyek]
```

Sumber resmi untuk ditinjau:

- https://developers.google.com/youtube/terms/developer-policies
- https://developers.google.com/youtube/terms/derived-metrics-policy
- [Catatan peninjauan proyek](policy-review.md)

Jika teman tidak mengetahui dasar penggunaan yang berlaku, minta penanggung jawab penelitian meninjaunya dan menyediakan catatan yang benar. API key hanya menyediakan akses teknis. Checkbox, status akademik, atau jawaban chatbot tidak otomatis membuktikan seluruh hak analisis/penyimpanan/penggabungan. Tetap bisa mengerjakan kandidat dan data manual dalam mode offline sambil menyiapkan dasar penggunaan nyata.

**Klik Simpan pengaturan setelah mengubah form.** Untuk mencoba metadata saja, aktifkan operasi metadata; tidak perlu mengaktifkan seluruh operasi sekaligus. Untuk langkah berikutnya, aktifkan hanya operasi yang memang dicakup dasar penggunaan proyek.

## 4. Arti pesan pada screenshot

Pesan versi lama:

> Document the requested data-use scope and policy review; packages require retention of 1-30 days

Artinya: **pengaturan penggunaan data untuk langkah yang dipilih belum lengkap**. Ada satu atau lebih kemungkinan: operasi belum dicentang, tanggal tinjauan kosong, referensi kosong, status tinjauan belum tercatat lengkap, atau retensi tidak berupa bilangan bulat 1–30. Pesan lama menggabungkan semua kemungkinan, sehingga gambar itu saja tidak menunjukkan kolom mana yang bermasalah.

Pesan tersebut tidak membuktikan key salah, kuota habis, atau YouTube menolak permintaan. Pemeriksaan ini dilakukan aplikasi sebelum permintaan API untuk langkah tersebut.

Cara menanganinya:

1. Buka **Pengaturan & API**.
2. Periksa operasi yang dibutuhkan, tanggal tinjauan, referensi yang benar, serta retensi.
3. Pastikan mode offline hanya dinonaktifkan untuk penggunaan nyata yang dasarnya telah diperiksa.
4. Klik **Simpan pengaturan**.
5. Kembali ke kandidat/dataset dan ulangi tombol sebelumnya.

Pada versi terbaru, halaman error menampilkan butir pengaturan yang belum terpenuhi dalam bahasa Indonesia serta tombol **Buka Pengaturan & API**. Tidak perlu mengedit JSON atau menghapus pemeriksaan dalam kode.

**Dua durasi yang berbeda:**

- **72 jam:** komentar yang diterbitkan sejak video terbit hingga sebelum 72 jam berikutnya. Ini menentukan komentar mana yang layak untuk analisis.
- **1–30 hari:** batas menyimpan paket data hasil pengambilan dan turunannya. Mengubahnya tidak mengubah jendela komentar menjadi 30 hari.

## 5. Tambahkan link kandidat

1. Buka **Kandidat & verifikasi**.
2. Tempel satu link Short pada **Link YouTube Short**.
3. Isi nama karakter bila sudah diketahui.
4. Klik **Tambah sebagai pending**.

Kandidat awal yang perlu diaudit:

```text
https://youtube.com/shorts/-2um93gmb3A
```

Link ini hanya kandidat; jangan langsung menyatakan included. Jika sudah ada di daftar, klik **Buka / edit** pada baris tersebut. Duplikat link ditolak agar tidak menciptakan event ganda.

Jika kelak mengubah link video pada kandidat yang sama, simpan perubahan dan ambil ulang metadata. Perubahan video mengosongkan bukti API lama serta mengembalikan status pending.

## 6. Ambil metadata melalui API

1. Buka detail kandidat.
2. Klik **Ambil / refresh metadata**.
3. Tunggu halaman proses menampilkan selesai.
4. Klik **Lihat kandidat**, kemudian **Buka / edit** kandidat tadi.
5. Periksa judul, channel ID, **Kanal resmi cocok**, waktu publikasi UTC, dan tanggal kedaluwarsa metadata.

Tanggal publikasi berasal dari API, bukan diketik manual berdasarkan judul, percakapan, atau hasil pencarian. Kecocokan kanal resmi harus benar. API metadata tidak membuktikan format Shorts ataupun bahwa konten adalah pengumuman awal.

Jika key/kuota/jaringan bermasalah, baca error dan perbaiki penyebabnya. Jangan mengganti metadata dengan tebakan agar verifikasi lolos.

## 7. Isi verifikasi manusia

Tonton video, pastikan berasal dari kanal resmi, lalu cari bukti pengumuman awal karakter. Tujuannya memisahkan pengumuman awal/drip marketing dari teaser, demo, dan unggahan lain.

| Kolom pada detail kandidat | Yang diisi |
|---|---|
| **Nama karakter** | Nama berdasarkan video dan bukti yang diperiksa. |
| **Sumber pengumuman awal** | URL bukti pengumuman awal, termasuk lintas platform bila relevan. Boleh sama dengan Short hanya jika memang bukti menunjukkan itu pengumuman awal. |
| **Waktu pengumuman awal UTC** | Timestamp dari sumber tersebut. Terpisah dari waktu publikasi Short yang diambil API. |
| **Jenis konten** | **Short pengumuman awal, sudah diperiksa** hanya jika pemeriksaan manusia mendukungnya. Untuk teaser/demo pilih kategori yang sesuai dan keluarkan. |
| **Status** | Pilih menurut tabel status di bawah. |
| **Alasan pengecualian** | Wajib untuk excluded atau no_matching_short. |
| **Catatan bukti & pemeriksa** | Tulis apa yang diperiksa, URL/bukti pendukung, pemeriksa dan tanggal, serta alasan keputusan. Jangan memasukkan data pribadi komentator. |

| Status | Kapan digunakan |
|---|---|
| **pending** | Bukti atau metadata belum lengkap, atau masih ragu. |
| **included** | Bukti manual lengkap, metadata API kanal resmi sesuai, publikasi Januari–September 2026, dan benar Short pengumuman awal. |
| **excluded** | Sudah diperiksa dan tidak memenuhi kriteria; isi alasan. |
| **no_matching_short** | Setelah penelusuran tidak ditemukan Short yang sesuai; isi alasan/hasil pencarian. |

Klik **Simpan verifikasi**. Jika included ditolak karena bukti belum lengkap, lengkapi bagian yang benar-benar tersedia atau simpan pending. Jangan mengisi teaser/demo untuk menutup kekosongan event.

Untuk mencatat pengumuman tanpa Short yang sesuai: tambahkan kandidat dengan nama karakter dan link kosong, lalu isi keputusan no_matching_short serta alasan. Record ini mendokumentasikan hasil audit dan tidak menjadi sumber pengumpulan komentar.

### Format timestamp dan waktu Indonesia

Format UTC: `YYYY-MM-DDTHH:MM:SSZ`. Huruf `Z` berarti UTC.

Contoh format **ilustratif, bukan timestamp kandidat**: `2026-03-01T04:00:00Z` = 1 Maret 2026 pukul 11.00 WIB. Untuk mengubah waktu lokal ke UTC, kurangi 7 jam dari WIB, 8 dari WITA, atau 9 dari WIT. Perhatikan perubahan tanggal ketika melewati tengah malam. Jika sumber tidak memberikan waktu yang cukup jelas, catat ketidakpastian dan pertahankan pending.

## 8. Catat penelusuran Januari–September 2026

Buka **Cakupan bulanan**. Untuk tiap bulan:

- **not_started:** belum ditelusuri.
- **partial:** sebagian penelusuran sudah dilakukan.
- **completed:** penelusuran selesai menurut prosedur penelitian; wajib isi waktu pemeriksaan UTC dan catatan bukti/strategi pencarian.

Klik **Simpan cakupan**. Menemukan satu video belum berarti penelusuran seluruh bulan lengkap. Bulan tanpa event dan bulan yang belum diperiksa harus tetap dibedakan. Bagian ini boleh dilengkapi bertahap; satu uji pengumpulan tidak membutuhkan klaim pencarian semua bulan selesai.

## 9. Ambil komentar secara otomatis

Syarat awal: key tersedia, pengaturan penggunaan lengkap, operasi pengumpulan aktif, ada kandidat included, dan 72 jam setelah publikasi sudah berlalu.

1. Di **Pengaturan & API**, aktifkan **Kumpulkan komentar utama** jika tercakup dasar penggunaan, lalu simpan.
2. Buka **Komentar & NLP**.
3. Lihat jumlah event included. Untuk uji satu kandidat, pilih **Semua event included (boleh untuk uji kecil)**.
4. Klik **Mulai pengumpulan**.
5. Tunggu proses selesai; jangan menutup server. Status menampilkan jumlah halaman dan komentar unik.
6. Klik **Lihat dataset**, lalu **Buka** pada dataset baru.
7. Periksa pagination/status pengumpulan: harus **lengkap** untuk masuk NLP utama.

**Pilot temporal** dipakai ketika sudah ada minimal enam event; aplikasi memilih 6–8 event yang tersebar menurut waktu. Dengan satu kandidat, jangan memilih pilot karena akan ditolak. Pilihan Semua mengambil semua event included yang ada, bukan memilih satu dari banyak event.

Yang dikerjakan kode:

- Mengecek ulang kanal dan publikasi video melalui API.
- Mengambil komentar tingkat utama melalui `commentThreads.list`, maksimum 100 komentar per halaman, hingga pagination selesai. Angka 100 bukan batas total komentar.
- Menghapus duplikat berdasarkan comment ID.
- Menyimpan status kelayakan berdasarkan `[publikasi, publikasi + 72 jam)`; komentar di luar jendela ditandai excluded.
- Mengecualikan dari analisis utama komentar yang diedit pada/selepas batas akhir jendela.
- Mencatat pengambilan lengkap atau terputus. Bahasa disaring pada tahap NLP; balasan dan profil penulis tidak disimpan.

Endpoint komentar tidak menyediakan filter tanggal. Karena video lama mungkin memiliki banyak komentar terbaru, pengambilan bisa menelusuri banyak halaman meskipun analisis hanya memakai 72 jam pertama. Ini membutuhkan waktu, koneksi dan kuota API.

Jika pengambilan terputus, perbaiki penyebabnya, lalu buat pengambilan baru. Hasil parsial tetap tersimpan sampai dihapus/kedaluwarsa dan tidak masuk NLP utama. Tidak ada kelanjutan otomatis dari token lama. Setiap pengambilan membuat dataset baru; jangan mengklik berulang hanya karena proses memerlukan waktu.

Data retrospektif hanya mencakup komentar yang masih dapat diakses saat diambil; tidak mengembalikan komentar yang sudah dihapus dan tidak merekonstruksi seluruh keadaan historis.

## 10. Lanjutkan NLP dan evaluasi manusia

1. Di Pengaturan, aktifkan **Analisis sentimen dan evaluasi data nyata** jika dasarnya tersedia; simpan.
2. Buka dataset yang pagination-nya lengkap.
3. Klik **1. Jalankan NLP lokal**. Penggunaan pertama mengunduh model sekitar 500 MB; setelah itu memakai cache. Inferensi berjalan di laptop, bukan mengirim komentar ke API AI eksternal.
4. Baca jumlah prediksi positif/negatif/netral serta laporan eksklusi bahasa, waktu/edit, dan penanda spam/duplikasi. Bahasa utama Inggris; komentar bahasa lain/undetermined dilaporkan sebagai dikeluarkan. Prediksi bukan ground truth.
5. Buka **2. Anotasi manual**, lalu buat sampel hingga 200 komentar. Jumlah sebenarnya dapat lebih kecil jika komentar eligible sedikit.
6. Beri label manusia tanpa melihat prediksi. Positif = evaluasi menyukai, negatif = ketidaksukaan/kritik, netral = tanpa evaluasi jelas. Ambigu/off-topic ditandai terpisah. Simpan setiap halaman sebelum berpindah. Jika ada dua anotator, kerjakan independen dan selesaikan perbedaan melalui adjudikasi.
7. Klik **3. Evaluasi model**. Macro-F1 dan confusion matrix membutuhkan label manual; agreement dihitung bila dua set label tersedia. Hasil tidak muncul dari label manual kosong.

Pengunduhan model memerlukan akses ke Hugging Face dan CDN bobot. Jika gagal, periksa koneksi/ruang disk dan ulangi; jangan mengubah checksum atau mematikan verifikasi TLS. Hasil model pada YouTube tetap perlu evaluasi meskipun program berhasil berjalan.

## 11. Masukkan revenue dan baca hubungan bulanan

Buka **Revenue**. Isi satu bulan melalui form, atau unduh template dan impor CSV yang sudah diisi. Impor mengganti seri yang ada dan meminta konfirmasi.

| Kolom | Pengisian |
|---|---|
| `month` | `YYYY-MM`, satu baris per bulan. |
| `revenue_usd` | Angka USD tanpa pemisah ribuan. Kosong berarti hilang; nol berarti nilai nol. Jika sumber memakai juta USD, konversikan dan dokumentasikan satuannya. |
| `platform_scope`, `region_scope` | Cakupan platform mobile/wilayah yang benar-benar dijelaskan sumber; harus konsisten antarbulan. |
| `cn_android_included` | true/false/unknown sesuai dokumentasi sumber. |
| `cn_android_multiplier` | Isi hanya jika komponen estimasi tersebut relevan dan didukung sumber; jangan menebak. |
| `source_url` | URL seri sumber. Kandidat: https://revenue.ennead.cc/revenue, perlu diperiksa manual. |
| `retrieved_at` | Tanggal/timestamp saat angka diambil. |
| `revision_notes` | Satuan, komponen estimasi, nilai hilang atau revisi yang perlu dijelaskan. |
| `available_at_utc` | Waktu angka/revisi itu benar-benar tersedia dari sumber. Opsional untuk korelasi; wajib untuk forecasting. Jangan mengarang tanggal historis atau menyamakannya dengan tanggal pengambilan sekarang. |

Jangan mencampur seri dengan cakupan berbeda atau mengarang angka agar grafik terisi.

Setelah NLP dan evaluasi manual, aktifkan operasi penggabungan eksternal jika dasarnya tersedia. Kembali ke dataset lalu klik **4. Analisis revenue t+1**.

Sentimen dikelompokkan menurut **bulan saat jendela 72 jam selesai**, kemudian dipasangkan dengan revenue bulan berikutnya. Karena itu kebutuhan revenue dapat melewati September 2026. Contoh konsep: jendela berakhir pada Agustus → pasangan revenue September; jendela berakhir pada Oktober → revenue November. Target yang belum selesai atau belum tersedia tidak dipaksakan menjadi pasangan.

Lihat jumlah pasangan aktual, bulan yang tidak terpasangkan, Spearman jika dapat dihitung, serta scatter berlabel bulan. Bulan tanpa event tidak diisi sentimen netral. Revenue tidak digandakan ke tiap komentar. Hubungan ini bukan bukti sebab-akibat dan tidak menunjukkan seluruh pemain/pembayar terwakili.

**5. Forecast eksperimen** boleh berstatus **blocked**. Pemeriksaan memerlukan antara lain minimal delapan pasangan bulanan berurutan, variasi sentimen, penelusuran lengkap tanpa pending, dan waktu ketersediaan revenue yang terdokumentasi. Ini ambang teknis, bukan jaminan ilmiah. Dengan satu kandidat atau seri kecil, blocked adalah hasil yang sesuai; jangan mengarang data untuk meloloskannya. Lihat [panduan lengkap](USER_GUIDE.md#11-forecasting-eksperimen) untuk batas hindcast/nowcast/forecast.

## 12. Menutup, menyimpan, dan melaporkan hasil trial

Data aplikasi ada di **`data/workbench/`**. Sesudah server ditutup, CSV/JSON tetap ada sampai dihapus atau kedaluwarsa; key dari form harus diisi ulang saat server dimulai. Metadata API kedaluwarsa memerlukan refresh/verifikasi ulang.

Paket data memiliki batas retensi maksimum 30 hari; kedaluwarsa dapat menghapus komentar, anotasi dan turunannya ketika aplikasi aktif dan tidak ada proses berjalan. Jika aplikasi tidak aktif, jadwalkan penghapusan secara terpisah. Ekspor dan cadangan di luar aplikasi juga mengikuti batas simpan dan tidak ditemukan purge otomatis. Jangan menganggap data akan disimpan permanen.

Menghapus kandidat juga menghapus dataset dan turunannya yang bergantung pada kandidat itu. Gunakan hanya pada data yang memang hendak dihapus; jangan menghapus kerja penelitian demi mencoba tombol.

Teman bisa mengirim laporan seperti ini:

```text
Branch/commit atau tanggal ZIP:
Versi Windows dan Python:
Menu/tombol yang dicoba:
Hasil: lulus / gagal / belum dicoba
Pesan error, jika ada:
Bagian panduan yang belum jelas:
```

Jangan menyertakan API key, cookie, komentar mentah atau data terbatas dalam laporan/screenshot. Gunakan [checklist pengujian](TESTING.md) untuk trial lebih lengkap. Keberhasilan tes offline atau API metadata belum membuktikan keberhasilan koleksi nyata maupun akurasi model sentimen.
