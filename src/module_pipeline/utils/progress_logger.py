"""
Progress Logger

A custom progress tracking utility designed to replace tqdm in environments where
dynamic progress bars are problematic (e.g., multi-process, non-interactive terminals).

It prints status logs at fixed time intervals instead of refreshing a single line.
"""

import time
from typing import Iterable, Optional


class ProgressLogger:
    """
    A progress tracker that logs status periodically.
    Compatible with tqdm's basic API.
    """

    def __init__(
        self,
        iterable: Optional[Iterable] = None,
        total: Optional[int] = None,
        desc: str = "Progress",
        interval: float = 10.0,
        unit: str = "it",
    ):
        """
        Initialize the ProgressLogger.

        Args:
            iterable: The iterable to wrap.
            total: Total number of items (optional if iterable has __len__).
            desc: Description prefix for log messages.
            interval: Minimum time interval (in seconds) between log prints.
            unit: Unit name for rate calculation (e.g., 'it', 'token').
        """
        self.iterable = iterable
        self.total = total
        if iterable is not None and self.total is None:
            try:
                self.total = len(iterable)
            except (TypeError, AttributeError):
                self.total = None

        self.desc = desc
        self.interval = interval
        self.unit = unit

        self.n = 0
        self.start_time = time.time()
        self.last_log_time = 0
        self.postfix = ""

    def __enter__(self):
        """Enter the context manager."""
        if self.last_log_time == 0:
            self.start_time = time.time()
            self.last_log_time = self.start_time
            self._log(f"Start processing {self.total if self.total else 'unknown'} {self.unit}s...")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context manager."""
        self._log_status(force=True)
        self._log(f"Finished. Total time: {self._format_time(time.time() - self.start_time)}")

    def __iter__(self):
        if self.last_log_time == 0:
            self.start_time = time.time()
            self.last_log_time = self.start_time
            self._log(f"Start processing {self.total if self.total else 'unknown'} {self.unit}s...")

        for item in self.iterable:
            yield item
            self.update(1)


    def update(self, n: int = 1):
        """Update progress by n."""
        self.n += n
        current_time = time.time()
        if current_time - self.last_log_time >= self.interval:
            self._log_status()
            self.last_log_time = current_time

    def set_postfix_str(self, s: str):
        """Set additional info to be displayed."""
        self.postfix = s

    def write(self, msg: str):
        """Print a message cleanly (mimics tqdm.write)."""
        print(msg)

    def _log_status(self, force: bool = False):
        """Calculate metrics and print status log."""
        current_time = time.time()
        if not force and current_time - self.last_log_time < self.interval:
            return

        elapsed = current_time - self.start_time
        rate = self.n / elapsed if elapsed > 0 else 0
        remaining = (self.total - self.n) / rate if self.total and rate > 0 else 0

        status_str = f"[{self.desc}] {self.n}"
        if self.total:
            status_str += f"/{self.total}"
            status_str += f" ({self.n / self.total * 100:.1f}%)"

        status_str += f" | {rate:.2f} {self.unit}/s"
        status_str += f" | Elapsed: {self._format_time(elapsed)}"

        if self.total:
            status_str += f" | ETA: {self._format_time(remaining)}"

        if self.postfix:
            status_str += f" | {self.postfix}"

        self._log(status_str)

    def close(self):
        """Close the progress logger (mimics tqdm.close)."""
        self._log_status(force=True)
        self._log(f"Finished. Total time: {self._format_time(time.time() - self.start_time)}")

    def _log(self, msg: str):
        print(f"- {msg}")

    @staticmethod
    def _format_time(seconds: float) -> str:
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{int(h)}:{int(m):02d}:{int(s):02d}"
        return f"{int(m):02d}:{int(s):02d}"
