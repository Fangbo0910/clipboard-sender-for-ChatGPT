import ctypes
import importlib.util
import subprocess
import sys
from pathlib import Path


# GUI entry point and dependency bootstrap.
MB_OK = 0x00000000
MB_YESNO = 0x00000004
MB_ICONWARNING = 0x00000030
MB_ICONERROR = 0x00000010
IDYES = 6


def _message_box(title, message, style):
    return ctypes.windll.user32.MessageBoxW(0, message, title, style)


# Check and install runtime dependencies if missing.
def _check_dependencies():
    requirements_path = Path(__file__).resolve().parent / "requirements.txt"
    dependencies = [
        ("PySide6", "PySide6"),
        ("playwright", "playwright"),
        ("requests", "requests"),
        ("win32clipboard", "pywin32"),
    ]
    missing = [pkg for module, pkg in dependencies if importlib.util.find_spec(module) is None]
    if not missing:
        return True

    message = "检测到依赖缺失：\n" + "\n".join(missing) + "\n\n是否一键安装？"
    if _message_box("依赖缺失", message, MB_YESNO | MB_ICONWARNING) != IDYES:
        return False

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            capture_output=True,
            text=True,
        )
    except Exception as exc:
        _message_box("安装失败", f"无法执行安装：{exc}", MB_OK | MB_ICONERROR)
        return False

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "未知错误"
        _message_box("安装失败", f"安装失败：\n{detail}", MB_OK | MB_ICONERROR)
        return False

    missing_again = [pkg for module, pkg in dependencies if importlib.util.find_spec(module) is None]
    if missing_again:
        _message_box("安装失败", "仍有依赖缺失，请重试。", MB_OK | MB_ICONERROR)
        return False

    return True


def main():
    if not _check_dependencies():
        return

    from PySide6 import QtWidgets

    from browser_bridge import BrowserBridge
    from clipboard_monitor import ClipboardMonitor
    from sites import EDGE_DEBUG_COMMAND

    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("剪切板发送器 v3.0")
            self.setMinimumSize(320, 160)

            self._browser = BrowserBridge()
            self._monitor = ClipboardMonitor(interval_ms=300)
            self._monitor.text_changed.connect(self._on_clipboard_text)

            self._running = False
            self._dialog_open = False

            self._start_button = QtWidgets.QPushButton("开始")
            self._pause_button = QtWidgets.QPushButton("暂停")
            self._author_button = QtWidgets.QPushButton("作者：fangbo")
            self._pause_button.setEnabled(False)

            self._start_button.clicked.connect(self._start)
            self._pause_button.clicked.connect(self._pause)
            self._author_button.clicked.connect(self._open_author_page)

            layout = QtWidgets.QVBoxLayout()
            layout.addStretch()
            layout.addWidget(self._start_button)
            layout.addWidget(self._pause_button)
            layout.addWidget(self._author_button)
            layout.addStretch()

            container = QtWidgets.QWidget()
            container.setLayout(layout)
            self.setCentralWidget(container)

            self._tray = QtWidgets.QSystemTrayIcon(self)
            self._tray.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))
            tray_menu = QtWidgets.QMenu()
            exit_action = tray_menu.addAction("退出")
            exit_action.triggered.connect(self._exit_app)
            self._tray.setContextMenu(tray_menu)
            self._tray.activated.connect(self._on_tray_activated)
            self._tray.show()

        # Hide to tray instead of closing the app.
        def closeEvent(self, event):
            event.ignore()
            self.hide()

        def _on_tray_activated(self, reason):
            if reason == QtWidgets.QSystemTrayIcon.Trigger:
                if self.isVisible():
                    self.hide()
                else:
                    self.show()
                    self.raise_()
                    self.activateWindow()

        def _start(self):
            if self._running:
                return
            if not self._ensure_debug_port():
                return
            self._browser.connect()
            if not self._ensure_target_site():
                return
            self._monitor.start()
            self._running = True
            self._start_button.setEnabled(False)
            self._pause_button.setEnabled(True)

        def _pause(self):
            if not self._running:
                return
            self._monitor.stop()
            self._running = False
            self._start_button.setEnabled(True)
            self._pause_button.setEnabled(False)

        # Open the author page in a new Edge tab.
        def _open_author_page(self):
            if not self._ensure_debug_port():
                return
            self._browser.connect()
            result = self._browser.open_author_page()
            if result != "ok":
                self._show_message("打开失败", "无法打开作者主页，请重试。")

        def _on_clipboard_text(self, text):
            if not self._running or self._dialog_open:
                return
            result = self._browser.send_text(text)
            if result == "ok":
                return
            if result in {"no_site", "no_input"}:
                self._handle_missing_site()
                return
            if result == "send_failed":
                self._show_message("发送失败", "无法发送内容，请重试。")

        def _handle_missing_site(self):
            self._monitor.stop()
            self._running = False
            self._start_button.setEnabled(True)
            self._pause_button.setEnabled(False)

            while True:
                retry = self._show_retry_exit(
                    "未检测到网站",
                    "未检测到网站",
                    None,
                )
                if not retry:
                    self._exit_app()
                    return
                if not self._ensure_debug_port():
                    return
                self._browser.connect()
                if self._ensure_target_site():
                    self._monitor.start()
                    self._running = True
                    self._start_button.setEnabled(False)
                    self._pause_button.setEnabled(True)
                    return

        def _ensure_target_site(self):
            page, _site = self._browser.find_target_page()
            if page is None:
                self._show_retry_exit("未检测到网站", "未检测到网站", None)
                return False
            return True

        def _ensure_debug_port(self):
            if self._browser.is_debug_port_available():
                return True
            self._show_retry_exit(
                "未检测到调试端口",
                "未检测到 Edge 调试端口，请使用以下命令启动 Edge：",
                EDGE_DEBUG_COMMAND,
            )
            return False

        def _show_retry_exit(self, title, message, detail):
            if self._dialog_open:
                return False
            self._dialog_open = True
            dialog = QtWidgets.QMessageBox(self)
            dialog.setIcon(QtWidgets.QMessageBox.Warning)
            dialog.setWindowTitle(title)
            dialog.setText(message)
            if detail:
                dialog.setDetailedText(detail)
            retry_button = dialog.addButton("重试", QtWidgets.QMessageBox.AcceptRole)
            exit_button = dialog.addButton("退出", QtWidgets.QMessageBox.RejectRole)
            dialog.exec()
            clicked_retry = dialog.clickedButton() == retry_button
            if dialog.clickedButton() == exit_button:
                clicked_retry = False
            self._dialog_open = False
            return clicked_retry

        def _show_message(self, title, message):
            dialog = QtWidgets.QMessageBox(self)
            dialog.setIcon(QtWidgets.QMessageBox.Information)
            dialog.setWindowTitle(title)
            dialog.setText(message)
            dialog.addButton("确定", QtWidgets.QMessageBox.AcceptRole)
            dialog.exec()

        def _exit_app(self):
            self._monitor.stop()
            self._browser.close()
            QtWidgets.QApplication.quit()

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
