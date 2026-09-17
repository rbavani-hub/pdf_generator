"""FastAPI application for Meeting Notes to PDF conversion."""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from services.ai_processor import process_meeting_notes, check_ollama_connection, get_available_models
from services.transcriber import get_transcriber
from services.pdf_generator import get_pdf_generator

# Initialize FastAPI app
app = FastAPI(
    title="Meeting Notes to PDF",
    description="Convert meeting notes into professional PDFs using local AI",
    version="1.0.0"
)

# Setup directories
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}

# HTML Templates
from fastapi.responses import HTMLResponse

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meeting Notes to PDF</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            opacity: 0.9;
            font-size: 1.1em;
        }

        .content {
            padding: 40px;
        }

        .tabs {
            display: flex;
            margin-bottom: 30px;
            border-bottom: 2px solid #e5e7eb;
        }

        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 1em;
            font-weight: 500;
            color: #6b7280;
            transition: all 0.3s;
            border-bottom: 3px solid transparent;
        }

        .tab:hover {
            color: #2563eb;
        }

        .tab.active {
            color: #2563eb;
            border-bottom-color: #2563eb;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .form-group {
            margin-bottom: 25px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #374151;
        }

        .form-group textarea {
            width: 100%;
            min-height: 200px;
            padding: 15px;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-family: inherit;
            font-size: 1em;
            resize: vertical;
            transition: border-color 0.3s;
        }

        .form-group textarea:focus {
            outline: none;
            border-color: #2563eb;
        }

        .file-upload {
            border: 3px dashed #d1d5db;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: #f9fafb;
        }

        .file-upload:hover {
            border-color: #2563eb;
            background: #eff6ff;
        }

        .file-upload.dragover {
            border-color: #2563eb;
            background: #eff6ff;
        }

        .file-upload input[type="file"] {
            display: none;
        }

        .file-upload .icon {
            font-size: 3em;
            margin-bottom: 15px;
        }

        .file-upload .text {
            color: #6b7280;
        }

        .file-upload .text strong {
            color: #2563eb;
        }

        .file-info {
            margin-top: 15px;
            padding: 10px;
            background: #ecfdf5;
            border-radius: 8px;
            display: none;
        }

        .file-info.show {
            display: block;
        }

        .btn {
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
            width: 100%;
            justify-content: center;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.4);
        }

        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .model-select {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        .model-select select {
            flex: 1;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 1em;
            background: white;
        }

        .status {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }

        .status.show {
            display: block;
        }

        .status.loading {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #1e40af;
        }

        .status.success {
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
            color: #065f46;
        }

        .status.error {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #991b1b;
        }

        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #bfdbfe;
            border-radius: 50%;
            border-top-color: #2563eb;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .footer {
            text-align: center;
            padding: 20px;
            background: #f9fafb;
            color: #6b7280;
            font-size: 0.9em;
        }

        .connection-status {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 15px;
            background: #f0fdf4;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 0.9em;
            color: #166534;
        }

        .connection-status.error {
            background: #fef2f2;
            color: #991b1b;
        }

        .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #22c55e;
        }

        .connection-status.error .dot {
            background: #ef4444;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Meeting Notes to PDF</h1>
            <p>Transform your meeting notes into professional documents using local AI</p>
        </div>

        <div class="content">
            <div id="connectionStatus" class="connection-status">
                <div class="dot"></div>
                <span>Checking Ollama connection...</span>
            </div>

            <div class="model-select">
                <select id="modelSelect">
                    <option value="qwen2.5:3b">qwen2.5:3b (Recommended)</option>
                </select>
            </div>

            <div class="tabs">
                <button class="tab active" data-tab="text">📝 Text Notes</button>
                <button class="tab" data-tab="audio">🎙️ Audio File</button>
            </div>

            <div id="textTab" class="tab-content active">
                <form id="textForm">
                    <div class="form-group">
                        <label for="meetingText">Paste your meeting notes below:</label>
                        <textarea id="meetingText" placeholder="Example:&#10;&#10;Meeting about Q4 planning with John, Sarah, and Mike.&#10;&#10;Discussed budget allocation for marketing campaigns.&#10;Decided to increase social media spend by 20%.&#10;&#10;Action items:&#10;- John: Create budget proposal by Friday&#10;- Sarah: Research new ad platforms&#10;- Mike: Schedule follow-up meeting"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary" id="processTextBtn">
                        <span>📄 Generate PDF</span>
                    </button>
                </form>
            </div>

            <div id="audioTab" class="tab-content">
                <form id="audioForm">
                    <div class="form-group">
                        <div class="file-upload" id="fileUpload">
                            <div class="icon">📁</div>
                            <div class="text">
                                <strong>Click to upload</strong> or drag and drop<br>
                                MP3, WAV, M4A, OGG, FLAC (Max 100MB)
                            </div>
                            <input type="file" id="audioFile" accept=".mp3,.wav,.m4a,.ogg,.flac,.webm">
                        </div>
                        <div class="file-info" id="fileInfo">
                            <span id="fileName"></span>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary" id="processAudioBtn" disabled>
                        <span>🎙️ Transcribe & Generate PDF</span>
                    </button>
                </form>
            </div>

            <div id="status" class="status">
                <span id="statusText"></span>
            </div>
        </div>

        <div class="footer">
            Powered by Ollama + faster-whisper | All processing happens locally on your machine
        </div>
    </div>

    <script>
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(tab.dataset.tab + 'Tab').classList.add('active');
            });
        });

        // File upload handling
        const fileUpload = document.getElementById('fileUpload');
        const audioFile = document.getElementById('audioFile');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const processAudioBtn = document.getElementById('processAudioBtn');

        fileUpload.addEventListener('click', () => audioFile.click());

        fileUpload.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileUpload.classList.add('dragover');
        });

        fileUpload.addEventListener('dragleave', () => {
            fileUpload.classList.remove('dragover');
        });

        fileUpload.addEventListener('drop', (e) => {
            e.preventDefault();
            fileUpload.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                audioFile.files = e.dataTransfer.files;
                handleFileSelect();
            }
        });

        audioFile.addEventListener('change', handleFileSelect);

        function handleFileSelect() {
            if (audioFile.files.length) {
                const file = audioFile.files[0];
                fileName.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
                fileInfo.classList.add('show');
                processAudioBtn.disabled = false;
            }
        }

        // Status handling
        function showStatus(message, type = 'loading') {
            const status = document.getElementById('status');
            const statusText = document.getElementById('statusText');
            status.className = `status show ${type}`;
            statusText.innerHTML = type === 'loading' 
                ? `<span class="spinner"></span> ${message}`
                : message;
        }

        // Check Ollama connection
        async function checkConnection() {
            try {
                const response = await fetch('/api/check-connection');
                const data = await response.json();
                const statusEl = document.getElementById('connectionStatus');
                
                if (data.connected) {
                    statusEl.className = 'connection-status';
                    statusEl.innerHTML = '<div class="dot"></div><span>Ollama connected</span>';
                    
                    // Load available models
                    if (data.models && data.models.length) {
                        const select = document.getElementById('modelSelect');
                        select.innerHTML = data.models.map(m => 
                            `<option value="${m}">${m}</option>`
                        ).join('');
                    }
                } else {
                    statusEl.className = 'connection-status error';
                    statusEl.innerHTML = '<div class="dot"></div><span>Ollama not running. Please start Ollama first.</span>';
                }
            } catch (error) {
                const statusEl = document.getElementById('connectionStatus');
                statusEl.className = 'connection-status error';
                statusEl.innerHTML = '<div class="dot"></div><span>Cannot connect to server</span>';
            }
        }

        // Text form submission
        document.getElementById('textForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = document.getElementById('meetingText').value.trim();
            if (!text) {
                showStatus('Please enter meeting notes', 'error');
                return;
            }

            const model = document.getElementById('modelSelect').value;
            const btn = document.getElementById('processTextBtn');
            
            btn.disabled = true;
            showStatus('Processing meeting notes with AI...');

            try {
                const response = await fetch('/api/process-text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, model })
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `meeting-notes-${new Date().toISOString().slice(0,10)}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    showStatus('PDF generated successfully!', 'success');
                } else {
                    const error = await response.json();
                    showStatus(error.detail || 'Failed to generate PDF', 'error');
                }
            } catch (error) {
                showStatus('Error: ' + error.message, 'error');
            } finally {
                btn.disabled = false;
            }
        });

        // Audio form submission
        document.getElementById('audioForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const file = audioFile.files[0];
            if (!file) {
                showStatus('Please select an audio file', 'error');
                return;
            }

            const model = document.getElementById('modelSelect').value;
            const btn = document.getElementById('processAudioBtn');
            
            btn.disabled = true;
            showStatus('Transcribing audio... This may take a while.');

            const formData = new FormData();
            formData.append('file', file);
            formData.append('model', model);

            try {
                const response = await fetch('/api/process-audio', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `meeting-notes-${new Date().toISOString().slice(0,10)}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    showStatus('PDF generated successfully!', 'success');
                } else {
                    const error = await response.json();
                    showStatus(error.detail || 'Failed to generate PDF', 'error');
                }
            } catch (error) {
                showStatus('Error: ' + error.message, 'error');
            } finally {
                btn.disabled = false;
            }
        });

        // Initialize
        checkConnection();
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    return INDEX_HTML


@app.get("/api/check-connection")
async def check_connection():
    """Check if Ollama is running and return available models."""
    connected = await check_ollama_connection()
    models = await get_available_models() if connected else []
    return {"connected": connected, "models": models}


@app.post("/api/process-text")
async def process_text(request: Request):
    """Process text meeting notes and return PDF."""
    try:
        body = await request.json()
        text = body.get("text", "")
        model = body.get("model", "qwen2.5:3b")

        if not text.strip():
            raise HTTPException(status_code=400, detail="No text provided")

        # Process with AI
        meeting_data = await process_meeting_notes(text, model)

        # Generate PDF
        pdf_generator = get_pdf_generator()
        pdf_bytes = pdf_generator.generate_pdf_bytes(meeting_data)

        # Save to output directory
        output_path = OUTPUT_DIR / f"meeting_{uuid.uuid4().hex[:8]}.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        # Return PDF as response
        from fastapi.responses import Response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=meeting-notes-{datetime.now().strftime('%Y-%m-%d')}.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process-audio")
async def process_audio(
    file: UploadFile = File(...),
    model: str = Form("qwen2.5:3b")
):
    """Process audio file, transcribe, and return PDF."""
    try:
        # Validate file format
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in SUPPORTED_AUDIO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format. Supported: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
            )

        # Save uploaded file
        temp_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{file_ext}"
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            # Transcribe audio
            transcriber = get_transcriber()
            transcription = await transcriber.transcribe_to_text(str(temp_path))

            if not transcription.strip():
                raise HTTPException(status_code=400, detail="No speech detected in audio")

            # Process with AI
            meeting_data = await process_meeting_notes(transcription, model)

            # Generate PDF
            pdf_generator = get_pdf_generator()
            pdf_bytes = pdf_generator.generate_pdf_bytes(meeting_data)

            # Save to output directory
            output_path = OUTPUT_DIR / f"meeting_{uuid.uuid4().hex[:8]}.pdf"
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)

            # Return PDF as response
            from fastapi.responses import Response
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=meeting-notes-{datetime.now().strftime('%Y-%m-%d')}.pdf"
                }
            )

        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
