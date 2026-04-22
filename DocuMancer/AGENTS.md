# DocuMancer - Agent Guide

**Last updated:** 2026-03-05

## Project Overview

DocuMancer is a modern Electron application for document conversion and management, built with a hardened Python converter backend and Electron frontend.

**Key Capabilities:**
- Document conversion (PDF, Word, Excel, PowerPoint, Images)
- Secure sandboxed conversion process
- Cross-platform desktop app (Windows, macOS, Linux)
- FastAPI-based Python backend for conversion logic
- Electron frontend with preload security

## Hostile Audit Persistence

- Append every hostile-audit checkpoint and verification result to the root `PROGRESS_TRACKER.md`.
- Do not mark renderer, preload, or backend-auth fixes complete without a real command result, test run, syntax check, or screenshot saved under `proof/hostile-audit/<timestamp>/`.
- Reproduce before patching. If the original exploit path fails, record the failed method and the replacement verification path.
- Escape or structurally render user-controlled HTML-adjacent content; do not reintroduce raw DOM insertion of unsanitized data.
- If a scanner or service cannot run, record the exact blocker and fallback review path instead of implying success.

**Architecture Pattern:**
```
┌─────────────────────────────────────────────────────────┐
│  Electron Frontend                                      │
│  ├── Main Process (Node.js)                            │
│  │   └── Spawns Python backend on startup              │
│  ├── Preload Script (secure bridge)                    │
│  └── Renderer Process (React/Vanilla JS)               │
├─────────────────────────────────────────────────────────┤
│  Python Backend (FastAPI)                               │
│  ├── server.py - HTTP wrapper                          │
│  └── converter.py - Document conversion logic          │
├─────────────────────────────────────────────────────────┤
│  Conversion Stack                                       │
│  ├── LibreOffice (document formats)                    │
│  ├── Pillow (image processing)                         │
│  └── pypandoc (markdown conversions)                   │
└─────────────────────────────────────────────────────────┘
```

---

## Build / Run / Test Commands

### Prerequisites
- Node.js 20+ 
- Python 3.11+
- LibreOffice (for document conversion)

### Development Setup
```bash
# 1. Install Node.js dependencies
npm install

# 2. Install Python dependencies
pip install -r backend/requirements.txt

# 3. Run in development mode
npm run dev
# Starts Electron + spawns Python backend automatically
```

### Build Commands
```bash
# Lint frontend code
npm run lint

# Run backend tests
npm run test:backend

# Package app (unpacked directories)
npm run pack

# Create installers (.exe, .dmg, .AppImage, .deb)
npm run dist
```

### Python Backend Only
```bash
cd backend

# Run FastAPI server directly
uvicorn server:app --reload --port 8000

# Test conversion API
curl -X POST http://localhost:8000/convert \
  -F "file=@document.docx" \
  -F "output_format=pdf"
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend Shell** | Electron 28+ | Desktop app container |
| **Frontend UI** | HTML/CSS/JS | User interface |
| **Backend** | Python 3.11+ | Conversion logic |
| **API** | FastAPI | HTTP interface |
| **Documents** | LibreOffice | DOCX, XLSX, PPTX conversion |
| **Images** | Pillow | Image format conversion |
| **Markdown** | pypandoc | MD ↔ other formats |
| **Packaging** | electron-builder | Cross-platform builds |

---

## Project Structure

```
DocuMancer/
├── frontend/                     # Electron frontend
│   ├── electron-main.js         # Main process
│   ├── preload.js               # Secure preload bridge
│   ├── index.html               # UI HTML
│   ├── renderer.js              # Renderer logic
│   └── styles.css               # App styles
├── backend/                      # Python conversion service
│   ├── server.py                # FastAPI app
│   ├── converter.py             # Conversion logic
│   ├── requirements.txt         # Python deps
│   └── __init__.py
├── shared/                       # Shared utilities
├── assets/                       # App icons, images
├── tests/                        # Test suites
├── scripts/                      # Build scripts
├── docs/                         # Documentation
├── electron-builder.yml          # Build configuration
└── package.json                  # Node.js deps and scripts
```

---

## Critical Code Patterns

### Secure Preload Bridge
```javascript
// preload.js - Secure IPC bridge
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  convertFile: (filePath, outputFormat) => 
    ipcRenderer.invoke('convert-file', filePath, outputFormat),
  selectFile: () => 
    ipcRenderer.invoke('select-file'),
  onProgress: (callback) => 
    ipcRenderer.on('conversion-progress', callback)
});
```

### Main Process Spawns Python
```javascript
// electron-main.js
const { spawn } = require('child_process');

function startPythonBackend() {
  const pythonProcess = spawn('python', [
    'backend/server.py',
    '--port', '8765'  // Random high port to avoid conflicts
  ], {
    stdio: ['ignore', 'pipe', 'pipe']
  });
  
  pythonProcess.on('exit', (code) => {
    console.log(`Python backend exited: ${code}`);
  });
  
  return pythonProcess;
}
```

### FastAPI Conversion Endpoint
```python
# backend/server.py
from fastapi import FastAPI, File, UploadFile
from converter import convert_document

app = FastAPI()

@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    output_format: str = "pdf"
):
    result = await convert_document(file, output_format)
    return {
        "success": True,
        "output_path": result.path,
        "download_url": f"/download/{result.id}"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "documancer"}
```

### Conversion Logic
```python
# backend/converter.py
import subprocess
from pathlib import Path

async def convert_document(input_file: Path, output_format: str) -> Path:
    input_path = Path(input_file)
    output_path = input_path.with_suffix(f'.{output_format}')
    
    # Use LibreOffice for document conversion
    subprocess.run([
        'soffice',
        '--headless',
        '--convert-to', output_format,
        '--outdir', str(output_path.parent),
        str(input_path)
    ], check=True)
    
    return output_path
```

---

## Non-Obvious Gotchas

### 1. Python Backend Spawning
The Electron main process spawns Python on startup:
- Port is dynamically assigned (starts at 8765)
- If Python crashes, the conversion fails gracefully
- Python logs are piped to Electron's console

### 2. Preload Script Security
The preload script is the ONLY bridge between frontend and backend:
- No direct `require()` in renderer
- No direct `fs` access from frontend
- All communication via `ipcRenderer.invoke()`

This follows Electron security best practices.

### 3. LibreOffice Dependency
LibreOffice must be installed system-wide:
- Windows: Download from libreoffice.org
- macOS: `brew install libreoffice`
- Linux: `apt install libreoffice`

The app checks for `soffice` on startup and shows error if missing.

### 4. electron-builder Configuration
Build targets defined in `electron-builder.yml`:
```yaml
appId: com.reliantai.documancer
productName: DocuMancer
copyright: Copyright © 2024

mac:
  category: public.app-category.productivity
  target: dmg

win:
  target: nsis

linux:
  target:
    - AppImage
    - deb
```

### 5. Backend Requirements Pinning
Python dependencies are pinned for reproducibility:
```txt
# backend/requirements.txt
fastapi==0.109.0
uvicorn==0.27.0
pypandoc==1.11
Pillow==10.2.0
```

Always pin versions for Electron apps to avoid breakage.

### 6. File Size Limits
Electron's IPC has message size limits:
- Base64-encoded files can exceed limits
- Use file paths, not file contents over IPC
- Backend reads files directly from disk

### 7. Development vs Production
In development:
- Python runs from source
- Hot reload available
- Console logs visible

In production:
- Python bundled as executable
- No console window
- Logs written to file

### 8. Cross-Platform Path Handling
Always use Node.js `path` module:
```javascript
// CORRECT
const path = require('path');
const fullPath = path.join(__dirname, 'backend', 'server.py');

// WRONG
const fullPath = __dirname + '/backend/server.py';  // Breaks on Windows
```

---

## Configuration

### Environment Variables
```bash
# Backend port (optional, defaults to random)
DOCUMANCER_PORT=8765

# Python path (optional, defaults to 'python')
DOCUMANCER_PYTHON=/usr/bin/python3

# Debug mode
DOCUMANCER_DEBUG=true
```

### electron-builder.yml
```yaml
# Build configuration
directories:
  output: dist
  buildResources: assets

files:
  - frontend/**/*
  - backend/**/*
  - shared/**/*
  - node_modules/**/*
  - package.json

extraResources:
  - from: backend/
    to: backend/
    filter:
      - "**/*.py"
      - "requirements.txt"
```

---

## Testing Strategy

### Backend Tests
```bash
cd backend
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-fail-under=80
```

### Frontend Tests
```bash
# Electron testing with Playwright (if configured)
npm run test:e2e
```

### Manual Testing
```bash
# 1. Start dev mode
npm run dev

# 2. Test file selection
# 3. Test conversion
# 4. Verify output file
```

---

## Packaging & Distribution

### macOS (.dmg)
```bash
npm run dist
# Output: dist/DocuMancer-1.0.0.dmg
```

### Windows (.exe)
```bash
npm run dist
# Output: dist/DocuMancer Setup 1.0.0.exe
```

### Linux (.AppImage, .deb)
```bash
npm run dist
# Output: dist/DocuMancer-1.0.0.AppImage
#         dist/documancer_1.0.0_amd64.deb
```

### Code Signing (Production)
Configure in `electron-builder.yml`:
```yaml
mac:
  identity: "Developer ID Application: Your Name"

win:
  certificateFile: "cert.p12"
  certificatePassword: "password"
```

---

## Troubleshooting

### Python Backend Not Starting
```bash
# Check Python is available
python --version

# Check requirements installed
pip list | grep fastapi

# Run backend manually to see errors
python backend/server.py
```

### Conversion Fails
```bash
# Check LibreOffice installed
soffice --version

# Test conversion directly
soffice --headless --convert-to pdf document.docx
```

### IPC Communication Issues
- Check preload script loaded correctly
- Verify channel names match between main and renderer
- Check Electron security settings

---

## Reference

See root `AGENTS.md` for:
- Core commandments (integration build rules)
- Mode-specific guidelines
- Universal patterns across all ReliantAI projects
