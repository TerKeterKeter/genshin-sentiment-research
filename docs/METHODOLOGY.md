# Protokol dan batas metodologis

Pertanyaan: bagaimana sentimen komentar awal terhadap pengumuman karakter Genshin Impact, dan apakah agregat sentimen berhubungan dengan estimasi pendapatan mobile bulan berikutnya?

## Unit dan kriteria

Satu kanal @GenshinImpact, hanya Shorts pengumuman awal/drip marketing yang diverifikasi manusia. Periode kandidat publikasi 1 Januari–30 September 2026 UTC, periode final mengikuti audit. Waktu pengumuman lintas platform dipisahkan dari publikasi Short. Teaser/demo tidak menggantikan event yang hilang. Penelusuran bulanan, alasan pengecualian dan pending dicatat.

Komentar utama saja, jendela `[video_published_at, video_published_at + 72 jam)`, dengan updatedAt pada/selepas cutoff dikeluarkan. Endpoint menggunakan maxResults=100, order=time, textFormat=plainText dan seluruh pagination; filter waktu lokal. ID dideduplikasi; author name/avatar/profile dan replies tidak disimpan. textOriginal tidak diasumsikan tersedia. Likes adalah snapshot saat pengambilan, bukan bobot historis. Retrospeksi hanya melihat komentar yang masih dapat diakses, bukan rekonstruksi seluruh kondisi historis.

## NLP dan model

Whitespace/NFC dinormalisasi, negasi/emoji dipertahankan. Langdetect seed 42 menyeleksi English; non-English dan undetermined dilaporkan. Spam/duplikasi teks ditandai untuk pemeriksaan, tanpa menghapus semua teks identik. Komentar panjang dipotong 512 token dan jumlahnya dilaporkan. Flag spam tidak otomatis mengubah kelas atau eligibility.

Model CardiffNLP: [twitter-roberta-base-sentiment-latest](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest).

- Revision: `3216a57f2a0d9c45a2e6c20157c20c49fb4bf9c7`.
- Lisensi model card: **CC-BY-4.0**, diverifikasi 26 Oktober 2026 (Asia/Jakarta).
- Label model card/config: 0 negative, 1 neutral, 2 positive.
- Sumber: [model card pada revision tetap](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest/blob/3216a57f2a0d9c45a2e6c20157c20c49fb4bf9c7/README.md), [config](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest/blob/3216a57f2a0d9c45a2e6c20157c20c49fb4bf9c7/config.json).
- `pytorch_model.bin`: 501045531 bytes. SHA-256 dari pointer Git LFS resmi pada revision tersebut: `4d24a3e32a88ed1c4e5b789fc6644e2e767500554e954b27dccf52a8e762cbae`. Loader memverifikasi checksum sebelum memuat bobot.
- Attribution: CardiffNLP; Loureiro et al. (2022), *TimeLMs: Diachronic Language Models from Twitter*, dan Camacho-Collados et al. (2022), *TweetNLP*, sebagaimana dirujuk model card. Pertahankan atribusi/lisensi ketika mendistribusikan model atau hasil yang memerlukan atribusi.

Model sudah dilatih/fine-tuned oleh penerbitnya; proyek ini hanya inferensi lokal CPU, tanpa fine-tuning. Domain Twitter berbeda dari YouTube; prediksi bukan ground truth. Tidak memodelkan antusiasme, pull intention atau demografi/sifat sensitif pengguna.

## Pilot dan evaluasi

Pilot temporal memilih 6–8 event pada tanggal tersebar; pemilihan tidak melihat sentimen/revenue. Mode semua event mendukung dataset penuh atau uji teknis kecil. Seluruh komentar yang memenuhi syarat diutamakan; sampling hanya untuk anotasi.

Anotasi maksimum 200 komentar, seed 42, alokasi seimbang event × interval 0–24/24–48/48–72 jam hingga kapasitas strata. Prediksi model disembunyikan. Ambiguous/off-topic terpisah dari positive/negative/neutral; gold melalui adjudikasi manusia. Macro-F1, confusion matrix, ukuran gold dan skipped/unscored dilaporkan; Cohen κ hanya bila tersedia pasangan label memadai. Sampel seimbang strata bukan distribusi populasi tanpa pembobotan desain. Evaluasi terhadap set kecil atau kelas tidak lengkap tidak membuktikan akurasi populasi.

## Revenue dan hubungan

Impor manual satu seri dengan platform/region/CN Android/multiplier konsisten; provenance, retrieval, ketersediaan nilai dan revisi dicatat. Kandidat sumber https://revenue.ennead.cc/revenue belum diverifikasi sebagai seri lengkap oleh kode. Tidak ada angka empiris bawaan. Format valid bukan bukti sumber benar atau hak penggunaan terpenuhi.

Unit hubungan adalah **bulan**, bukan komentar. Agregasi memakai bulan saat jendela selesai; semua komentar eligible berbobot sama, event dengan banyak komentar lebih dominan. net sentiment = positive proportion − negative proportion. Bulan tanpa event, nol komentar, revenue hilang dan sentiment netral dibedakan. Agregat t dipasangkan dengan revenue t+1 yang bulannya selesai; jumlah pasangan aktual dan missing reasons dicatat. Scatter berlabel bulan dan Spearman eksploratif. Tidak menggandakan revenue bulanan ke baris komentar untuk inferensi independen.

Bukan kausal, komentator bukan representasi seluruh pemain/pembayar. Tren waktu, serial dependence, update, rerun dan beda cakupan audiens/revenue dapat mendistorsi asosiasi. Jendela akhir September dapat masuk Oktober dan dipasangkan dengan revenue November; bulan yang belum selesai tidak diperlakukan sebagai angka penuh.

## Forecasting, perubahan cakupan yang disetujui

Forecasting semula ditunda. Pengguna kemudian secara eksplisit meminta eksperimen sederhana dengan peringatan dan pemeriksaan kecukupan; impor massal link tidak disetujui dan tidak dibuat.

Ridge alpha=1.0 memakai satu fitur net sentiment; StandardScaler fit hanya pada training. Baseline naïf memakai target revenue terakhir yang tersedia. Ambang minimal 8 pasangan berurutan, minimal 4 titik training dan 3 origin hindcast, tanggal available_at_utc revenue terdokumentasi, scope pencarian lengkap serta tidak ada pending. Tidak ada hyperparameter search atau random train/test split. Ambang ini untuk demonstrasi perangkat lunak, bukan power calculation dan bukan klaim dataset cukup secara ilmiah.

Training setiap origin hanya memakai target yang tersedia sebelum target bulan uji dimulai. Fitur sentimen tetap direkonstruksi dari komentar retrospektif yang bertahan; hindcast bukan validasi real-time lengkap. Tidak ada klaim mengetahui komentar yang dihapus atau versi revenue yang tidak diarsipkan. Versi/revisi nilai yang dipakai harus didukung provenance.

Prediksi target masa lalu/sudah diketahui ditolak sebagai forecast masa depan. Estimasi bulan berjalan dilabeli nowcast; future target dilabeli forecast bila memang sesudah tanggal analisis. Kinerja MAE dibandingkan naïf; model yang tidak mengalahkan baseline ditandai. Tidak ada proyeksi per karakter, jaminan hasil atau interval kepercayaan rekaan. Model dapat tetap blocked karena dataset sembilan bulan tidak memenuhi syarat.
