# Panduan anotasi pilot

Positif: evaluasi menyukai/mendukung karakter atau pengumuman. Negatif: ketidaksukaan/kritik terhadap karakter/pengumuman. Netral: informasi atau pertanyaan tanpa evaluasi yang jelas. Jangan otomatis menjadikan niat gacha atau popularitas sebagai sentimen.

Tandai ambiguous terpisah untuk sarkasme, emosi campuran atau konteks tidak cukup; off_topic terpisah jika komentar tidak membahas objek penelitian. Keduanya bukan kelas sentimen keempat. Jangan memaksakan gold pada ambigu yang belum diselesaikan: kosongkan adjudicated_label sampai adjudikasi. Dokumentasikan aturan pengecualian sebelum evaluasi.

Template anotasi tidak memperlihatkan prediksi/score model. Jika dua anotator tersedia, kerjakan independen. Prediksi tersimpan terpisah dan CLI evaluate menggabungkannya berdasarkan ID saat evaluasi. Selesaikan perbedaan melalui adjudikasi. Evaluasi hanya baris dengan gold sah dan prediksi; laporkan jumlah yang tidak berlabel/ambigu/off-topic secara terpisah. Macro-F1 dan confusion matrix berurutan positive, negative, neutral. Cohen kappa menggunakan pasangan label kedua anotator; kappa tidak terdefinisi pada label konstan dan harus dilaporkan demikian. Label model bukan ground truth.

Sampling seimbang per event × interval dapat berbeda dari distribusi populasi komentar; hasil evaluasi merupakan diagnosis pilot, bukan estimasi akurasi populasi tanpa penyesuaian desain. Jangan otomatis membuang semua teks identik: tinjau spam dan dokumentasikan keputusan.
