import time

import win32clipboard
from PySide6 import QtCore


# Polls Windows clipboard for new text.
class ClipboardMonitor(QtCore.QObject):
    text_changed = QtCore.Signal(str)

    def __init__(self, interval_ms=300, parent=None):
        super().__init__(parent)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._poll)
        self._last_text = None

    def start(self):
        if not self._timer.isActive():
            self._timer.start()

    def stop(self):
        if self._timer.isActive():
            self._timer.stop()

    def _poll(self):
        text = self._read_text()
        if text is None:
            return
        if text == "":
            return
        if text == self._last_text:
            return
        self._last_text = text
        self.text_changed.emit(text)

    @staticmethod
    def _read_text():
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            else:
                data = None
        except Exception:
            data = None
        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass
        return data
