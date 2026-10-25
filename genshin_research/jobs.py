"""One background job at a time, with browser polling and safe public errors."""

import threading
import uuid


class Jobs:
    def __init__(self):
        self.lock = threading.Lock()
        self.items = {}

    def busy(self):
        with self.lock:
            return any(r["status"] == "running" for r in self.items.values())

    def start(self, title, function):
        with self.lock:
            if any(r["status"] == "running" for r in self.items.values()):
                raise ValueError("Masih ada proses berjalan. Tunggu hingga selesai.")
            job_id = uuid.uuid4().hex
            self.items[job_id] = dict(
                title=title, status="running", message="Memulai...", result=None
            )

        def progress(message):
            with self.lock:
                self.items[job_id]["message"] = message

        def work():
            try:
                result = function(progress)
                with self.lock:
                    self.items[job_id].update(
                        status="done", message="Selesai", result=result
                    )
            except Exception as error:
                # Requests errors are sanitized in the API adapter. Do not expose stack traces/URLs.
                message = (
                    str(error)
                    if isinstance(
                        error,
                        (ValueError, PermissionError, RuntimeError, FileNotFoundError),
                    )
                    else f"Proses gagal ({type(error).__name__}); periksa instalasi dan dataset."
                )
                with self.lock:
                    self.items[job_id].update(status="error", message=message)

        threading.Thread(target=work, daemon=True).start()
        return job_id

    def get(self, job_id):
        with self.lock:
            return dict(self.items[job_id]) if job_id in self.items else None
