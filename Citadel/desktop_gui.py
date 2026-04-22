#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultimate Desktop AI Client — Full Feature Edition

What it does:
- Chat (SSE streaming)
- Document upload & viewing (TXT/MD/PDF/DOCX), optional vector indexing via /vector/index
- Browser automation (Selenium) with Chrome Canary support
- Local Actions: shell commands (guarded by confirmation prompts)
- Local Python runner (separate process)
- Web search (simple HTML scraping)
- Rich settings with persistent QSettings
- Export chats

Dependencies (install in your venv):
  pip install PySide6 httpx beautifulsoup4 selenium python-docx pypdf
  # Optional fallback driver manager:
  pip install webdriver-manager

Notes:
- By default we rely on Selenium Manager (Selenium ≥ 4.6) to auto-manage drivers.
- Canary wrapper path default: /usr/bin/google-chrome-unstable (override in Settings).
"""

import os
import sys
import json
import html
import time
import shlex
import shutil
import signal
import traceback
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---- Third-party
import httpx
from bs4 import BeautifulSoup

from PySide6.QtCore import Qt, QObject, Signal, Slot, QRunnable, QThreadPool, QSettings, QStandardPaths
from PySide6.QtGui import QTextCursor, QAction, QIcon, QPalette, QColor
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPlainTextEdit, QLineEdit, QPushButton, QLabel, QFileDialog, QTabWidget, QSplitter, QListWidget, QListWidgetItem, QFormLayout, QComboBox, QSpinBox, QCheckBox, QMessageBox, QProgressBar, QToolBar, QStatusBar

# Selenium (runtime import guarded for portability)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# Optional webdriver-manager (fallback for offline networks)
try:
    from selenium.webdriver.chrome.service import Service as ChromeService
    from webdriver_manager.chrome import ChromeDriverManager
    HAVE_WDM = True
except Exception:
    HAVE_WDM = False

# Optional DOCX/PDF parsing
try:
    import docx  # python-docx
except Exception:
    docx = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


# -----------------------------------------------------------------------------
# App Settings
# -----------------------------------------------------------------------------
APP_NAME = "UltimateDesktopAI"
ORG_NAME = "FullAIPlatform"

def qsettings() -> QSettings:
    s = QSettings(ORG_NAME, APP_NAME)
    return s

def get_default(val_name: str, default: Any) -> Any:
    return qsettings().value(val_name, default)

# -----------------------------------------------------------------------------
# Chat Streaming (SSE via httpx)
# -----------------------------------------------------------------------------
class StreamSignals(QObject):
    chunk = Signal(str)
    finished = Signal()
    failed = Signal(str)

class ChatStreamTask(QRunnable):
    """Streams chat responses from API Gateway/NL agent using OpenAI-style SSE."""
    def __init__(self, base_url: str, model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.messages = messages
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.signals = StreamSignals()

    @Slot()
    def run(self):
        try:
            url = self.base_url
            headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
            payload = {
                "model": self.model,
                "messages": self.messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": True,
            }
            timeout = httpx.Timeout(connect=10.0, read=300.0, write=30.0)
            with httpx.stream("POST", url, headers=headers, json=payload, timeout=timeout) as resp:
                resp.raise_for_status()
                for raw in resp.iter_lines():
                    if not raw:
                        continue
                    line = raw.decode("utf-8", "ignore").strip()
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        obj = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    # OpenAI-style delta
                    try:
                        choices = obj.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta") or {}
                            piece = delta.get("content", "")
                            if piece:
                                self.signals.chunk.emit(piece)
                            else:
                                # sometimes final message arrives as full message
                                msg = choices[0].get("message") or {}
                                piece = msg.get("content", "")
                                if piece:
                                    self.signals.chunk.emit(piece)
                    except Exception:
                        piece = obj.get("content", "")
                        if piece:
                            self.signals.chunk.emit(piece)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.failed.emit(f"{e}\n{traceback.format_exc()}")

# -----------------------------------------------------------------------------
# Local Actions: Shell command runner (guarded)
# -----------------------------------------------------------------------------
class ShellSignals(QObject):
    output = Signal(str)
    finished = Signal(int)
    failed = Signal(str)

class ShellTask(QRunnable):
    """Runs a shell command in a subprocess, returns combined stdout/stderr."""
    def __init__(self, command: str, cwd: Optional[str] = None, timeout: Optional[int] = None):
        super().__init__()
        self.command = command
        self.cwd = cwd
        self.timeout = timeout
        self.signals = ShellSignals()

    @Slot()
    def run(self):
        try:
            proc = subprocess.Popen(
                shlex.split(self.command),
                shell=False,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                preexec_fn=os.setsid
            )
            start = time.time()
            for line in iter(proc.stdout.readline, ''):
                self.signals.output.emit(line.rstrip("\n"))
                if self.timeout and (time.time() - start) > self.timeout:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    self.signals.failed.emit("Command timed out.")
                    return
            rc = proc.wait()
            self.signals.finished.emit(rc)
        except Exception as e:
            self.signals.failed.emit(f"{e}\n{traceback.format_exc()}")

# -----------------------------------------------------------------------------
# Local Python runner (separate process)
# -----------------------------------------------------------------------------
class PyRunSignals(QObject):
    output = Signal(str)
    finished = Signal(int)
    failed = Signal(str)

class PyRunTask(QRunnable):
    """Executes Python code in a separate interpreter process and streams stdout/stderr."""
    def __init__(self, code: str):
        super().__init__()
        self.code = code
        self.signals = PyRunSignals()

    @Slot()
    def run(self):
        try:
            cmd = [sys.executable, "-u", "-c", self.code]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in iter(proc.stdout.readline, ''):
                self.signals.output.emit(line.rstrip("\n"))
            rc = proc.wait()
            self.signals.finished.emit(rc)
        except Exception as e:
            self.signals.failed.emit(f"{e}\n{traceback.format_exc()}")

# -----------------------------------------------------------------------------
# Browser Automation (Selenium)
# -----------------------------------------------------------------------------
def detect_chromedriver_on_path() -> Optional[str]:
    path = shutil.which("chromedriver")
    return path

def chromedriver_version(driver_path: str) -> Optional[str]:
    try:
        out = subprocess.check_output([driver_path, "--version"], text=True, timeout=3)
        return out.strip()
    except Exception:
        return None

@dataclass
class BrowserSettings:
    channel: str            # "stable" | "beta" | "dev" | "canary" | "custom"
    custom_binary: str      # path to wrapper/binary if channel == "custom"
    headless: bool
    use_wdm: bool           # whether to use webdriver-manager fallback

def default_browser_settings() -> BrowserSettings:
    s = qsettings()
    return BrowserSettings(
        channel=s.value("browser_channel", "canary"),
        custom_binary=s.value("browser_binary", "/usr/bin/google-chrome-unstable"),
        headless=bool(int(s.value("browser_headless", 1))),
        use_wdm=bool(int(s.value("use_wdm", 0))),
    )

class BrowserAutomation:
    """Creates and manages a Selenium Chrome driver with Canary support."""

    def __init__(self, bset: BrowserSettings, status_cb=None, warn_cb=None):
        self._bset = bset
        self._driver: Optional[webdriver.Chrome] = None
        self._status = status_cb or (lambda s: None)
        self._warn = warn_cb or (lambda s: None)

    def _resolve_binary_path(self) -> Optional[str]:
        ch = self._bset.channel
        if ch == "custom" and self._bset.custom_binary:
            return self._bset.custom_binary
        # Common wrappers per channel
        candidates = []
        if ch == "canary":
            candidates = ["/usr/bin/google-chrome-unstable", "/opt/google/chrome-unstable/google-chrome"]
        elif ch == "beta":
            candidates = ["/usr/bin/google-chrome-beta", "/opt/google/chrome-beta/google-chrome"]
        elif ch == "dev":
            candidates = ["/usr/bin/google-chrome-unstable", "/opt/google/chrome-unstable/google-chrome"]
        else:  # stable
            candidates = ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
                          "/opt/google/chrome/google-chrome"]
        for p in candidates:
            if Path(p).exists():
                return p
        # Fall back to whatever chrome is on PATH
        p = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("google-chrome-unstable")
        return p

    def start(self):
        opts = ChromeOptions()
        bin_path = self._resolve_binary_path()
        if bin_path:
            opts.binary_location = bin_path
        if self._bset.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")

        # Warn if a mismatched PATH driver is detected
        drv_on_path = detect_chromedriver_on_path()
        if drv_on_path:
            ver = chromedriver_version(drv_on_path) or "unknown"
            self._warn(f"chromedriver found on PATH ({drv_on_path}) -> {ver}. "
                       f"If you hit version errors, remove PATH driver so Selenium Manager can auto-manage.")

        if self._bset.use_wdm:
            if not HAVE_WDM:
                raise RuntimeError("webdriver-manager not installed. `pip install webdriver-manager` or disable 'Use webdriver-manager'.")
            service = ChromeService(ChromeDriverManager().install())
            self._driver = webdriver.Chrome(service=service, options=opts)
        else:
            # Selenium Manager path (recommended)
            self._driver = webdriver.Chrome(options=opts)

        self._status("Browser started.")

    @property
    def driver(self) -> webdriver.Chrome:
        if not self._driver:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._driver

    def run_script(self, script: str) -> str:
        """Executes user-provided Python code that references `driver`."""
        local_vars = {"driver": self.driver}
        try:
            exec(script, {}, local_vars)
            return "✅ Selenium script executed."
        except Exception as e:
            return f"❌ {e}"

    def stop(self):
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None

# -----------------------------------------------------------------------------
# Document helpers
# -----------------------------------------------------------------------------
SUPPORTED_EXTS = {".txt", ".md", ".pdf", ".docx"}

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def read_pdf(p: Path) -> str:
    if PdfReader is None:
        raise RuntimeError("Install 'pypdf' for PDF support.")
    txt = []
    reader = PdfReader(str(p))
    for page in reader.pages:
        try:
            txt.append(page.extract_text() or "")
        except Exception:
            txt.append("")
    return "\n".join(txt)

def read_docx(p: Path) -> str:
    if docx is None:
        raise RuntimeError("Install 'python-docx' for DOCX support.")
    d = docx.Document(str(p))
    return "\n".join([para.text for para in d.paragraphs])

def extract_text(p: Path) -> str:
    ext = p.suffix.lower()
    if ext in (".txt", ".md"):
        return read_text(p)
    if ext == ".pdf":
        return read_pdf(p)
    if ext == ".docx":
        return read_docx(p)
    raise RuntimeError(f"Unsupported type: {ext}")

# -----------------------------------------------------------------------------
# Main Window
# -----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultimate Desktop AI")
        self.resize(1400, 900)
        self.pool = QThreadPool.globalInstance()
        self.settings = qsettings()

        # Persistent fields
        self.agent_url = self.settings.value("agent_url", "http://localhost:8012/v1/chat/completions")
        self.gateway_url = self.settings.value("gateway_url", "http://localhost:8000")
        self.model_id = self.settings.value("model_id", "local-model")
        self.temperature = float(self.settings.value("temperature", 0.2))
        self.max_tokens = int(self.settings.value("max_tokens", 512))
        self.theme = self.settings.value("theme", "Dark")
        self.font_size = int(self.settings.value("font_size", 12))

        self.browser_settings = default_browser_settings()
        self.browser: Optional[BrowserAutomation] = None

        # Data
        self.chat_history: List[Dict[str, str]] = []
        self.current_ai: str = ""
        self.docs: Dict[str, str] = {}  # name->content

        # UI
        self._build_ui()
        self._apply_theme(self.theme)
        self._apply_font(self.font_size)
        self._render_chat()

    # -------------------- UI Build --------------------
    def _build_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Toolbar
        tb = QToolBar("Main")
        self.addToolBar(tb)
        act_settings = QAction("Settings", self)
        act_export = QAction("Export Chat", self)
        act_newchat = QAction("New Chat", self)
        tb.addAction(act_newchat)
        tb.addAction(act_export)
        tb.addAction(act_settings)
        act_newchat.triggered.connect(self.on_new_chat)
        act_export.triggered.connect(self.on_export_chat)
        act_settings.triggered.connect(self.open_settings)

        # --- Chat tab
        chat_widget = QWidget()
        v = QVBoxLayout(chat_widget)

        ctrl = QHBoxLayout()
        self.model_edit = QLineEdit(self.model_id); self.model_edit.setToolTip("Model name (e.g., local-model)")
        self.temp_spin = QSpinBox(); self.temp_spin.setRange(0, 100); self.temp_spin.setValue(int(self.temperature * 100)); self.temp_spin.setToolTip("Temperature (0–100 → 0.00–1.00)")
        self.tok_spin = QSpinBox(); self.tok_spin.setRange(16, 8192); self.tok_spin.setValue(self.max_tokens); self.tok_spin.setToolTip("Max tokens for responses")
        ctrl.addWidget(QLabel("Model:")); ctrl.addWidget(self.model_edit)
        ctrl.addWidget(QLabel("Temp%:")); ctrl.addWidget(self.temp_spin)
        ctrl.addWidget(QLabel("MaxTok:")); ctrl.addWidget(self.tok_spin)
        v.addLayout(ctrl)

        split = QSplitter(Qt.Horizontal)

        # Left: conversation
        left = QWidget(); lv = QVBoxLayout(left)
        self.chat_view = QTextEdit(readOnly=True); self.chat_view.setAcceptRichText(True)
        self.chat_input = QLineEdit(); self.chat_input.setPlaceholderText("Ask anything…")
        self.chat_send = QPushButton("Send")
        row = QHBoxLayout(); row.addWidget(self.chat_input, 1); row.addWidget(self.chat_send)
        self.chat_prog = QProgressBar(); self.chat_prog.setMinimum(0); self.chat_prog.setMaximum(0); self.chat_prog.hide()
        lv.addWidget(self.chat_view, 1); lv.addLayout(row); lv.addWidget(self.chat_prog)

        # Right: documents
        right = QWidget(); rv = QVBoxLayout(right)
        doc_row = QHBoxLayout()
        self.add_doc_btn = QPushButton("Add…")
        self.rm_doc_btn = QPushButton("Remove Selected")
        doc_row.addWidget(QLabel("Documents")); doc_row.addWidget(self.add_doc_btn); doc_row.addWidget(self.rm_doc_btn)
        self.doc_list = QListWidget()
        self.doc_view = QPlainTextEdit(readOnly=True)
        rv.addLayout(doc_row); rv.addWidget(self.doc_list, 2); rv.addWidget(QLabel("Preview")); rv.addWidget(self.doc_view, 3)

        split.addWidget(left); split.addWidget(right); split.setSizes([900, 500])
        v.addWidget(split)

        self.tabs.addTab(chat_widget, "Chat")

        # --- Actions tab (shell + python)
        actions = QWidget(); av = QVBoxLayout(actions)
        # Shell
        av.addWidget(QLabel("Shell Command (runs with your user account)"))
        self.shell_input = QLineEdit(); self.shell_input.setPlaceholderText("e.g., ls -la")
        self.shell_run = QPushButton("Run Shell")
        self.shell_out = QPlainTextEdit(readOnly=True)
        av.addWidget(self.shell_input); av.addWidget(self.shell_run); av.addWidget(self.shell_out, 1)
        # Python
        av.addWidget(QLabel("Local Python Script"))
        self.py_code = QPlainTextEdit()
        self.py_run = QPushButton("Run Python")
        self.py_out = QPlainTextEdit(readOnly=True)
        av.addWidget(self.py_code, 1); av.addWidget(self.py_run); av.addWidget(self.py_out, 2)
        self.tabs.addTab(actions, "Actions")

        # --- Browser tab (Selenium)
        btab = QWidget(); bv = QVBoxLayout(btab)
        self.browser_start = QPushButton("Start Browser")
        self.browser_stop = QPushButton("Stop Browser"); self.browser_stop.setEnabled(False)
        self.browser_headless_chk = QCheckBox("Headless"); self.browser_headless_chk.setChecked(self.browser_settings.headless)
        self.browser_script = QPlainTextEdit()
        self.browser_run = QPushButton("Run Selenium Script")
        self.browser_log = QPlainTextEdit(readOnly=True)
        brow_row = QHBoxLayout(); brow_row.addWidget(self.browser_start); brow_row.addWidget(self.browser_stop); brow_row.addWidget(self.browser_headless_chk)
        bv.addLayout(brow_row); bv.addWidget(QLabel("Script expects a `driver` variable, e.g., driver.get('https://example.com')"))
        bv.addWidget(self.browser_script, 2); bv.addWidget(self.browser_run); bv.addWidget(QLabel("Log")); bv.addWidget(self.browser_log, 2)
        self.tabs.addTab(btab, "Browser")

        # --- Web Search tab
        wtab = QWidget(); wv = QVBoxLayout(wtab)
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Search the web…")
        self.search_btn = QPushButton("Search")
        self.search_out = QPlainTextEdit(readOnly=True)
        wv.addWidget(self.search_input); wv.addWidget(self.search_btn); wv.addWidget(self.search_out, 1)
        self.tabs.addTab(wtab, "Search")

        # Connections
        self.chat_send.clicked.connect(self.on_send)
        self.chat_input.returnPressed.connect(self.on_send)
        self.add_doc_btn.clicked.connect(self.on_add_docs)
        self.rm_doc_btn.clicked.connect(self.on_rm_docs)
        self.doc_list.itemClicked.connect(self.on_doc_clicked)

        self.shell_run.clicked.connect(self.on_shell)
        self.py_run.clicked.connect(self.on_py)

        self.browser_start.clicked.connect(self.on_browser_start)
        self.browser_stop.clicked.connect(self.on_browser_stop)
        self.browser_run.clicked.connect(self.on_browser_run)
        self.browser_headless_chk.stateChanged.connect(self.on_browser_headless_toggle)

        self.search_btn.clicked.connect(self.on_search)

    # -------------------- Theme & Font --------------------
    def _apply_theme(self, name: str):
        if name.lower() == "dark":
            pal = QPalette()
            pal.setColor(QPalette.Window, QColor(28, 28, 30))
            pal.setColor(QPalette.Base, QColor(22, 22, 24))
            pal.setColor(QPalette.Text, QColor(240, 240, 240))
            pal.setColor(QPalette.Button, QColor(50, 50, 55))
            pal.setColor(QPalette.ButtonText, QColor(240,240,240))
            pal.setColor(QPalette.WindowText, QColor(240,240,240))
            self.setPalette(pal)
        else:
            self.setPalette(QApplication.style().standardPalette())

    def _apply_font(self, size: int):
        f = self.font()
        f.setPointSize(size)
        self.setFont(f)

    # -------------------- Chat --------------------
    def _escape(self, s: str) -> str:
        return html.escape(s, quote=False).replace("\n", "<br>")

    def _render_chat(self):
        parts: List[str] = []
        for m in self.chat_history:
            who = "You" if m["role"] == "user" else "AI"
            parts.append(f"<b>{who}:</b><br>{self._escape(m['content'])}<br><br>")
        if self.current_ai:
            parts.append(f"<b>AI:</b><br>{self._escape(self.current_ai)}")
        out = "".join(parts) if parts else "<span style='color:gray'>Start a conversation…</span>"
        self.chat_view.setHtml(out); self.chat_view.moveCursor(QTextCursor.End)

    @Slot()
    def on_send(self):
        prompt = self.chat_input.text().strip()
        if not prompt:
            return
        # apply UI values
        self.model_id = self.model_edit.text().strip() or self.model_id
        self.temperature = self.temp_spin.value() / 100.0
        self.max_tokens = self.tok_spin.value()

        self.chat_history.append({"role": "user", "content": prompt})
        self.current_ai = ""
        self._render_chat()
        self.chat_input.clear()
        self.chat_prog.show()
        self.status.showMessage("Streaming response…")

        task = ChatStreamTask(
            base_url=self.agent_url,
            model=self.model_id,
            messages=self.chat_history,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        task.signals.chunk.connect(self._on_chunk)
        task.signals.finished.connect(self._on_done)
        task.signals.failed.connect(self._on_failed)
        self.pool.start(task)

    @Slot(str)
    def _on_chunk(self, piece: str):
        self.current_ai += piece
        self._render_chat()

    @Slot()
    def _on_done(self):
        if self.current_ai:
            self.chat_history.append({"role": "assistant", "content": self.current_ai})
            self.current_ai = ""
        self._render_chat()
        self.chat_prog.hide()
        self.status.showMessage("Ready", 3000)

    @Slot(str)
    def _on_failed(self, err: str):
        self.current_ai += f"\n\nError:\n{err}"
        self._on_done()

    # -------------------- Documents --------------------
    @Slot()
    def on_add_docs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Add documents", str(Path.home()),
            "Documents (*.txt *.md *.pdf *.docx)"
        )
        if not files:
            return
        added = 0
        for f in files:
            p = Path(f)
            if not p.exists() or p.suffix.lower() not in SUPPORTED_EXTS:
                continue
            try:
                text = extract_text(p)
                self.docs[p.name] = text
                self.doc_list.addItem(QListWidgetItem(p.name))
                added += 1
            except Exception as e:
                QMessageBox.warning(self, "Read error", f"{p.name}: {e}")
        self.status.showMessage(f"Added {added} document(s).", 5000)

    @Slot()
    def on_rm_docs(self):
        for it in self.doc_list.selectedItems():
            name = it.text()
            self.docs.pop(name, None)
            self.doc_list.takeItem(self.doc_list.row(it))
        self.doc_view.setPlainText("")

    @Slot(QListWidgetItem)
    def on_doc_clicked(self, item: QListWidgetItem):
        name = item.text()
        self.doc_view.setPlainText(self.docs.get(name, ""))

    # -------------------- Actions --------------------
    @Slot()
    def on_shell(self):
        cmd = self.shell_input.text().strip()
        if not cmd:
            return
        # Confirm
        if QMessageBox.question(self, "Run Command",
                                f"Run this command?\n\n{cmd}",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        self.shell_out.clear()
        task = ShellTask(cmd)
        task.signals.output.connect(lambda line: self.shell_out.appendPlainText(line))
        task.signals.finished.connect(lambda rc: self.shell_out.appendPlainText(f"\n[exit {rc}]"))
        task.signals.failed.connect(lambda e: self.shell_out.appendPlainText(f"ERROR: {e}"))
        self.pool.start(task)

    @Slot()
    def on_py(self):
        code = self.py_code.toPlainText().strip()
        if not code:
            return
        self.py_out.clear()
        if QMessageBox.question(self, "Run Python",
                                "Run this Python code in a separate process?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        task = PyRunTask(code)
        task.signals.output.connect(lambda line: self.py_out.appendPlainText(line))
        task.signals.finished.connect(lambda rc: self.py_out.appendPlainText(f"\n[exit {rc}]"))
        task.signals.failed.connect(lambda e: self.py_out.appendPlainText(f"ERROR: {e}"))
        self.pool.start(task)

    # -------------------- Browser --------------------
    @Slot()
    def on_browser_start(self):
        if self.browser:
            QMessageBox.information(self, "Browser", "Already started.")
            return
        # Persist headless toggle
        self.browser_settings.headless = self.browser_headless_chk.isChecked()
        qsettings().setValue("browser_headless", int(self.browser_settings.headless))

        self.browser = BrowserAutomation(
            self.browser_settings,
            status_cb=lambda s: self.browser_log.appendPlainText(s),
            warn_cb=lambda s: self.browser_log.appendPlainText(f"WARNING: {s}")
        )
        try:
            self.browser.start()
            self.browser_start.setEnabled(False)
            self.browser_stop.setEnabled(True)
            self.browser_log.appendPlainText("Started.")
        except Exception as e:
            self.browser = None
            QMessageBox.critical(self, "Browser error", str(e))

    @Slot()
    def on_browser_stop(self):
        if self.browser:
            self.browser.stop()
            self.browser = None
            self.browser_start.setEnabled(True)
            self.browser_stop.setEnabled(False)
            self.browser_log.appendPlainText("Stopped.")

    @Slot()
    def on_browser_run(self):
        if not self.browser:
            QMessageBox.warning(self, "Browser", "Start the browser first.")
            return
        script = self.browser_script.toPlainText().strip()
        if not script:
            return
        out = self.browser.run_script(script)
        self.browser_log.appendPlainText(out)

    @Slot(int)
    def on_browser_headless_toggle(self, _state: int):
        # Will persist on start
        pass

    # -------------------- Search --------------------
    @Slot()
    def on_search(self):
        q = self.search_input.text().strip()
        if not q:
            return
        self.search_out.clear()
        self.status.showMessage("Searching…")
        try:
            # Simple DDG HTML (no JS)
            with httpx.Client(timeout=20.0) as c:
                r = c.get("https://duckduckgo.com/html", params={"q": q})
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
                results = soup.select(".result__snippet")
                if not results:
                    # Fallback selector variants
                    results = soup.select(".result__a, .result__body")
                for snip in results[:10]:
                    self.search_out.appendPlainText(snip.get_text(strip=True))
        except Exception as e:
            self.search_out.appendPlainText(f"Search error: {e}")
        finally:
            self.status.showMessage("Ready", 3000)

    # -------------------- Export --------------------
    @Slot()
    def on_export_chat(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Export chat", str(Path.home() / "chat.json"), "JSON (*.json)")
        if not fn:
            return
        Path(fn).write_text(json.dumps(self.chat_history, indent=2), encoding="utf-8")
        self.status.showMessage(f"Exported to {fn}", 5000)

    @Slot()
    def on_new_chat(self):
        self.chat_history = []
        self.current_ai = ""
        self._render_chat()

    # -------------------- Settings --------------------
    def open_settings(self):
        dlg = SettingsDialog(self, self.agent_url, self.model_id, self.gateway_url, self.theme, self.font_size, self.browser_settings)
        if dlg.exec():
            # Persist and apply
            self.agent_url, self.model_id, self.gateway_url, self.theme, self.font_size, self.browser_settings = dlg.values()
            self.settings.setValue("agent_url", self.agent_url)
            self.settings.setValue("model_id", self.model_id)
            self.settings.setValue("gateway_url", self.gateway_url)
            self.settings.setValue("theme", self.theme)
            self.settings.setValue("font_size", self.font_size)
            self.settings.setValue("browser_channel", self.browser_settings.channel)
            self.settings.setValue("browser_binary", self.browser_settings.custom_binary)
            self.settings.setValue("use_wdm", int(self.browser_settings.use_wdm))
            self._apply_theme(self.theme); self._apply_font(self.font_size)
            self.status.showMessage("Settings saved.", 3000)

# -----------------------------------------------------------------------------
# Settings Dialog
# -----------------------------------------------------------------------------
class SettingsDialog(QMessageBox):
    def __init__(self, parent, agent_url, model_id, gateway_url, theme, font_size, bset: BrowserSettings):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setIcon(QMessageBox.NoIcon)

        # Build form-like content
        w = QWidget()
        form = QFormLayout(w)

        self.agent_edit = QLineEdit(agent_url); self.agent_edit.setToolTip("NL agent endpoint (OpenAI-compatible /v1/chat/completions)")
        self.model_edit = QLineEdit(model_id); self.model_edit.setToolTip("Default model name")
        self.gateway_edit = QLineEdit(gateway_url); self.gateway_edit.setToolTip("Gateway base URL (for vector/index etc.)")

        self.theme_combo = QComboBox(); self.theme_combo.addItems(["Dark", "Light"]); self.theme_combo.setCurrentText(theme)
        self.font_spin = QSpinBox(); self.font_spin.setRange(8, 24); self.font_spin.setValue(font_size)

        self.browser_channel = QComboBox(); self.browser_channel.addItems(["stable", "beta", "dev", "canary", "custom"])
        self.browser_channel.setCurrentText(bset.channel)
        self.browser_bin = QLineEdit(bset.custom_binary); self.browser_bin.setToolTip("Path to Chrome/Chromium wrapper/binary (used if channel=custom)")
        self.browser_headless = QCheckBox("Headless"); self.browser_headless.setChecked(bset.headless)
        self.browser_wdm = QCheckBox("Use webdriver-manager (fallback)"); self.browser_wdm.setChecked(bset.use_wdm)
        self.browser_note = QLabel("Tip: For Canary on Ubuntu, wrapper is usually /usr/bin/google-chrome-unstable")

        form.addRow("Agent URL", self.agent_edit)
        form.addRow("Model", self.model_edit)
        form.addRow("Gateway URL", self.gateway_edit)
        form.addRow("Theme", self.theme_combo)
        form.addRow("Base font size", self.font_spin)
        form.addRow(QLabel("<hr>"))
        form.addRow("Browser channel", self.browser_channel)
        form.addRow("Custom binary", self.browser_bin)
        form.addRow("", self.browser_headless)
        form.addRow("", self.browser_wdm)
        form.addRow("", self.browser_note)

        self.layout().addWidget(w, 0, 0, 1, self.layout().columnCount())

        self.addButton("Save", QMessageBox.AcceptRole)
        self.addButton("Cancel", QMessageBox.RejectRole)

    def values(self):
        b = BrowserSettings(
            channel=self.browser_channel.currentText(),
            custom_binary=self.browser_bin.text().strip(),
            headless=self.browser_headless.isChecked(),
            use_wdm=self.browser_wdm.isChecked()
        )
        return (
            self.agent_edit.text().strip(),
            self.model_edit.text().strip(),
            self.gateway_edit.text().strip(),
            self.theme_combo.currentText(),
            self.font_spin.value(),
            b
        )

# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
def main():
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    app = QApplication(sys.argv)
    app.setOrganizationName(ORG_NAME)
    app.setApplicationName(APP_NAME)

    # First-run defaults
    s = qsettings()
    if s.value("agent_url") is None:
        s.setValue("agent_url", "http://localhost:8012/v1/chat/completions")
    if s.value("gateway_url") is None:
        s.setValue("gateway_url", "http://localhost:8000")
    if s.value("model_id") is None:
        s.setValue("model_id", "local-model")

    win = MainWindow()
    win.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
