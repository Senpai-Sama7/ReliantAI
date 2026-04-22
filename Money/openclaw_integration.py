"""
OpenClaw Integration Helpers

Provides lightweight utilities so OpenClaw automations can call the HVAC AI scripts,
gate credentials, and surface logs/errors before invoking orchestration tasks.
"""

import logging
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

logger = logging.getLogger("openclaw_integration")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(handler)


def _run_command(command: list[str], cwd: Path | None = None, env: dict | None = None) -> None:
    cmd = " ".join(command)
    logger.info("Running: %s", cmd)
    subprocess.run(command, cwd=cwd, env=env or os.environ, check=True)


class OpenClawOrchestrator:
    def __init__(self, project_root: Path | None = None, port: int = 8888):
        self.project_root = (project_root or Path(__file__).resolve().parent)
        self.port = port
        self.openclaw = shutil.which("openclaw")
        if not self.openclaw:
            logger.warning("OpenClaw CLI not found. Automation will only run local scripts.")

    def _project_python(self) -> str:
        if os.name == "nt":
            candidate = self.project_root / ".venv" / "Scripts" / "python.exe"
        else:
            candidate = self.project_root / ".venv" / "bin" / "python"
        if candidate.exists():
            return str(candidate)
        return sys.executable or "python"

    def start_gateway(self) -> None:
        if not self.openclaw:
            logger.info("Skipping gateway start (CLI missing).")
            return
        _run_command([self.openclaw, "start", "--headless"], cwd=self.project_root)

    def validate_credentials(self) -> None:
        required = [
            "GEMINI_API_KEY", "LANGSMITH_API_KEY", "TWILIO_SID", "TWILIO_TOKEN",
            "TWILIO_FROM_PHONE", "COMPOSIO_API_KEY", "OWNER_PHONE",
            "TECH_PHONE_NUMBER", "DISPATCH_API_KEY",
        ]
        missing = [key for key in required if not os.environ.get(key)]
        if missing:
            raise RuntimeError(f"Missing credentials: {', '.join(missing)}")

    def run_triage_flow(self, message: str, temp: int) -> None:
        env = os.environ.copy()
        env["TASK_MESSAGE"] = message
        env["TASK_TEMP"] = str(temp)
        python = self._project_python()
        # Use consistent script calling
        _run_command([python, "tools/test_suite.py"], cwd=self.project_root, env=env)
        _run_command([python, "tools/roi_calculator.py"], cwd=self.project_root, env=env)
        self.post_dispatch(env.get("DISPATCH_API_KEY", ""), env)

    def post_dispatch(self, api_key: str, env: dict | None = None) -> None:
        if not api_key:
            raise RuntimeError("Cannot call /dispatch without DISPATCH_API_KEY")
        url = f"http://127.0.0.1:{self.port}/dispatch"
        payload = b'{"message":"OpenClaw automation dispatch"}'
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
        }
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, data=payload) as resp:
            logger.info("Dispatch response %s %s", resp.status, resp.reason)

    def run_dispatch_smoke(self) -> None:
        _run_command(
            [self._project_python(), "hvac_dispatch_crew.py", "--message", "OpenClaw smoke test", "--temp", "80"],
            cwd=self.project_root,
        )

    def run_quality_gates(self) -> None:
        python = self._project_python()
        _run_command([python, "tools/test_suite.py"], cwd=self.project_root)
        _run_command([python, "-m", "pytest", "tools/test_component_security.py"], cwd=self.project_root)
        # audit_component_tests.py is in archive/, skip or update if needed.
        # logger.info("Skipping audit_component_tests (Archived).")

    def stream_logs(self) -> None:
        log_path = Path(self.project_root) / "hvac_dispatch.log"
        if not log_path.exists():
            logger.info("Log file missing; nothing to stream.")
            return
        lines = log_path.read_text().splitlines()
        for line in lines[-40:]:
            logger.info(line)
