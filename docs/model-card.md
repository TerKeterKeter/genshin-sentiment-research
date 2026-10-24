# Model pilihan dan status verifikasi

Model kandidat: `cardiffnlp/twitter-roberta-base-sentiment-latest`.
Model card: https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest

Tujuan: inferensi lokal sentimen bahasa Inggris tiga kelas, tanpa fine-tuning.
Pemetaan yang diharapkan (wajib cocokkan model card/config): negative → negative, neutral → neutral, positive → positive.

Status: belum diverifikasi. Akses endpoint metadata/card diblokir proxy HTTP 403 pada sesi implementasi. Revision SHA immutable dan lisensi **belum diketahui**; jangan mengisinya dari tebakan. `model_revision=null` dan placeholder lisensi membuat inferensi gagal secara sengaja.

Sebelum menjalankan inferensi, catat tanggal akses, commit SHA penuh, lisensi dan ketentuannya, label aktual, bahasa/domain pelatihan dan keterbatasan pada halaman ini; perbarui `config.json`. Jangan mematikan pemeriksaan TLS. Token model tidak wajib diasumsikan untuk model publik. Bahasa slang, sarkasme, emoji, campuran sentimen dan domain YouTube memerlukan evaluasi manual. Komentar panjang dipotong pada 512 token dengan penanda eksplisit; laporkan jumlah pemotongan.
