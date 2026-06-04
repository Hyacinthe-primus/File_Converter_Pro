"""
Conversion Worker

Runs any conversion workload in a background QThread so the UI
never freezes.  Drop-in replacement for the blocking for-loops
that previously ran on the main thread.

Usage (from app.py):
    from conversion_worker import ConversionWorker

    self._worker = ConversionWorker(tasks, runner_fn)
    self._worker.progress.connect(self.progress_bar.setValue)
    self._worker.file_done.connect(self._on_file_done)
    self._worker.finished.connect(self._on_conversion_finished)
    self._worker.error.connect(self._on_conversion_error)
    self._worker.start()

"""

from PySide6.QtCore import QThread, Signal

class ConversionWorker(QThread):
    """
    Generic background worker for file conversions.
    """

    progress = Signal(int)

    file_done = Signal(dict)

    finished = Signal(dict)

    error = Signal(str)

    def __init__(self, tasks: list, runner_fn, parent=None):
        super().__init__(parent)
        self._tasks     = tasks
        self._runner_fn = runner_fn
        self._abort     = False

    def abort(self):
        """Request a graceful stop after the current file finishes."""
        self._abort = True

    def run(self):
        import time
        t0            = time.perf_counter()
        total         = len(self._tasks)
        success_count = 0
        failed        = []

        for task in self._tasks:
            if self._abort:
                break
            try:
                result = self._runner_fn(task)
            except Exception as exc:
                result = {"success": False, "error": str(exc)}

            result.update(task)

            if result.get("success"):
                success_count += 1
            else:
                failed.append({
                    "name":  task.get("input_path", "?"),
                    "error": result.get("error", "unknown error"),
                })

            idx = task.get("index", 0)
            self.progress.emit(int((idx + 1) / total * 100))
            self.file_done.emit(result)

        self.finished.emit({
            "success_count": success_count,
            "total":         total,
            "failed":        failed,
            "total_time":    time.perf_counter() - t0,
        })
