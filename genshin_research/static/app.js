'use strict';
const token = document.querySelector('meta[name="csrf-token"]').content;
for (const form of document.querySelectorAll('form[method="post"]')) {
  const input = document.createElement('input');
  input.type = 'hidden'; input.name = 'csrf'; input.value = token; form.append(input);
  form.addEventListener('submit', () => { const button = form.querySelector('button'); if (button) {button.disabled = true; button.textContent = 'Memproses…';} });
}
const panel = document.querySelector('#job-panel');
if (panel) {
  async function poll() {
    try {
      const response = await fetch(panel.dataset.statusUrl, {cache:'no-store'});
      if (!response.ok) throw new Error('Status belum dapat dibaca');
      const job = await response.json();
      document.querySelector('#job-state').textContent = job.status;
      document.querySelector('#job-message').textContent = job.message;
      document.querySelector('#job-result').textContent = job.result || '';
      if (job.status === 'running') setTimeout(poll, 1300);
    } catch (_) {document.querySelector('#job-message').textContent = 'Koneksi status terputus. Pastikan server tetap berjalan, lalu muat ulang halaman.';}
  }
  poll();
}
