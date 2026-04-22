#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Local Super Agent - Desktop GUI (Refactored)
---------------------------------------------

A standalone desktop application with a retro-futuristic, liquid-glass UI.
This version is refactored for responsiveness and a better user experience,
with agent logic running in a separate thread.
"""

import sys
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QHBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from qfluentwidgets import setTheme, Theme, MicaWindow, PrimaryPushButton, PushButton

# Ensure the agent can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from local_agent.agent import Agent

# --- Agent Worker Thread ---
class AgentWorker(QThread):
    """Runs the agent's processing logic in a separate thread to keep the GUI responsive."""
    response_ready = pyqtSignal(str)
    confirmation_required = pyqtSignal(str, dict)

    def __init__(self, agent_instance: Agent, messages: List[Dict[str, Any]]):
        super().__init__()
        self.agent = agent_instance
        self.messages = messages
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self._user_confirmation = False

    def run(self):
        """The main entry point for the thread's execution."""
        asyncio.run(self.agent.process_chat(
            self.messages,
            self._send_response_callback,
            self._send_confirmation_request_callback
        ))

    async def _send_response_callback(self, text: str):
        """Emits a signal to send a response to the main GUI thread."""
        self.response_ready.emit(text)

    async def _send_confirmation_request_callback(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """Emits a signal for confirmation and waits for the user's response."""
        self.mutex.lock()
        try:
            self.confirmation_required.emit(tool_name, parameters)
            self.condition.wait(self.mutex)  # Wait for the GUI thread to provide a response
            return self._user_confirmation
        finally:
            self.mutex.unlock()

    def set_confirmation(self, confirmed: bool):
        """Called by the main thread to set the user's confirmation and wake the worker."""
        self.mutex.lock()
        try:
            self._user_confirmation = confirmed
            self.condition.wakeOne()
        finally:
            self.mutex.unlock()


# --- Main Application Window ---
class MainWindow(MicaWindow):
    """The main window of the application."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Citadel - Local Super Agent")
        self.setWindowIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        self.resize(1000, 800)

        # --- UI Elements ---
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask the agent to do something...")
        self.send_button = PrimaryPushButton("Send")

        # --- Layout ---
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.chat_history, 1)
        main_layout.addLayout(input_layout)

        # --- Agent Instance & State ---
        self.agent = Agent()
        self.current_worker: Optional[AgentWorker] = None
        self.messages: List[Dict[str, str]] = []

        # --- Styling ---
        self.setStyleSheet("""
            QWidget { background-color: transparent; color: #E0E0E0; font-size: 16px; }
            QTextEdit { background-color: rgba(30, 30, 30, 0.8); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 10px; }
            QLineEdit { background-color: rgba(45, 45, 45, 0.9); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; padding: 10px; }
        """)

        # --- Connections ---
        self.send_button.clicked.connect(self.send_message)
        self.input_field.returnPressed.connect(self.send_message)

    def send_message(self):
        """Sends a message from the user to the agent."""
        message_text = self.input_field.text().strip()
        if not message_text:
            return

        self.input_field.clear()
        self.messages.append({"role": "user", "content": message_text})
        self._update_chat_display()

        # Disable input while the agent is working
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)

        self.current_worker = AgentWorker(self.agent, self.messages)
        self.current_worker.response_ready.connect(self.on_agent_response)
        self.current_worker.confirmation_required.connect(self.on_confirmation_required)
        self.current_worker.finished.connect(self.on_agent_finished)
        self.current_worker.start()

    def on_agent_response(self, text: str):
        """Handles a final response from the agent."""
        self.messages.append({"role": "assistant", "content": text})
        self._update_chat_display()

    def on_agent_finished(self):
        """Re-enables the input fields after the agent is done."""
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus()

    def on_confirmation_required(self, tool_name: str, parameters: Dict[str, Any]):
        """Displays a confirmation prompt to the user."""
        confirmation_html = f"""
            <div style='background-color: #4A4A4A; border-radius: 8px; padding: 10px; margin: 10px;'>
                <p style='color: #FFD700;'><b>CONFIRMATION REQUIRED</b></p>
                <p>The agent wants to run the tool: <b>{tool_name}</b></p>
                <pre style='background-color: #2E2E2E; padding: 8px; border-radius: 5px; color: #E0E0E0;'><code>{json.dumps(parameters, indent=2)}</code></pre>
                <p>Do you want to allow this action?</p>
            </div>
        """
        self.chat_history.append(confirmation_html)

        # Create a container for the buttons
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        allow_btn = PrimaryPushButton("Allow")
        deny_btn = PushButton("Deny")
        button_layout.addWidget(allow_btn)
        button_layout.addWidget(deny_btn)
        button_layout.addStretch(1)

        # Insert the button container widget into the QTextEdit
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertBlock()
        cursor.insertWidget(button_container)
        self.chat_history.ensureCursorVisible()

        # Connect signals to a handler that removes the buttons
        allow_btn.clicked.connect(lambda: self._handle_confirmation(True, button_container))
        deny_btn.clicked.connect(lambda: self._handle_confirmation(False, button_container))

    def _handle_confirmation(self, confirmed: bool, button_container: QWidget):
        """Handles the user's confirmation response."""
        if self.current_worker:
            self.current_worker.set_confirmation(confirmed)
            # Add a message to the history indicating the choice
            choice_text = "Allowed" if confirmed else "Denied"
            self.messages.append({"role": "user", "content": f"User action: {choice_text}"})
            self._update_chat_display()
        
        # Remove the button container from the UI
        button_container.setVisible(False)
        button_container.deleteLater()

    def _update_chat_display(self):
        """Renders the entire chat history."""
        html_content = ""
        for msg in self.messages:
            role = msg["role"]
            content = msg["content"].replace('<', '&lt;').replace('>', '&gt;')
            if role == "user":
                html_content += f"<p style='color: #87CEEB; text-align: right;'><b>You:</b> {content}</p>"
            elif role == "assistant":
                html_content += f"<p style='color: #E0E0E0;'><b>Agent:</b> {content}</p>"
            elif role == "tool":
                 html_content += f"<pre style='background-color: #333; color: #AEEA00; padding: 5px; border-radius: 5px;'><code>{content}</code></pre>"
        self.chat_history.setHtml(html_content)
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())

# --- Main Application Entry Point ---
def main():
    """Initializes and runs the Qt application."""
    # Necessary for high-DPI displays
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    setTheme(Theme.DARK)
    app = QApplication(sys.argv)
    
    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except (FileNotFoundError, ValueError) as e:
        # Catch pre-flight check errors from the agent
        logging.critical(f"A critical error occurred during startup: {e}")
        # A simple message box for critical startup errors
        from PyQt6.QtWidgets import QMessageBox
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText("Application Startup Error")
        msg_box.setInformativeText(str(e))
        msg_box.setWindowTitle("Error")
        msg_box.exec()
        sys.exit(1)


if __name__ == "__main__":
    main()
