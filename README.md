# Meeting Notes to PDF

Transform your meeting notes into professional, well-organized PDF documents using local AI. No cloud services required - everything runs on your machine.

## Features

- **Text Input**: Paste raw meeting notes and get a structured PDF
- **Audio Transcription**: Upload audio files (MP3, WAV, M4A) and get transcribed, organized PDFs
- **Local AI Processing**: Uses Ollama for intelligent note structuring
- **Professional PDF Output**: Clean, formatted documents with sections for:
  - Meeting title and date
  - Attendees
  - Agenda items
  - Discussion points
  - Decisions made
  - Action items with assignees
  - Follow-ups

## Prerequisites

### 1. Install Ollama

Ollama runs AI models locally on your machine.

**Windows/Mac/Linux:**
- Download from https://ollama.com
- Install and start Ollama

**Verify installation:**
```bash
ollama --version
```

### 2. Pull an AI Model

```bash
# Recommended (3GB, good balance of speed and quality)
ollama pull qwen2.5:3b

# Alternative - smaller/faster (2GB)
ollama pull llama3.2:1b

# Alternative - larger/better quality (4GB)
ollama pull qwen2.5:7b
```

### 3. Install Python Dependencies

```bash
cd meeting-to-pdf
pip install -r requirements.txt
```

**Note for Windows users:** If WeasyPrint fails to install, you may need to install GTK+ runtime. Download from: https://github.com/nicm/weasyprint/releases

## Usage

### Start the Application

```bash
python app.py
```

Open your browser and go to: http://localhost:8000

### Using Text Input

1. Click the "Text Notes" tab
2. Paste your meeting notes
3. Click "Generate PDF"
4. Download your professional PDF

### Using Audio Files

1. Click the "Audio File" tab
2. Upload an audio file (MP3, WAV, M4A, OGG, FLAC)
3. Click "Transcribe & Generate PDF"
4. Wait for transcription and processing
5. Download your professional PDF

## Example Input

```
Meeting about Q4 planning with John, Sarah, and Mike.

Discussed budget allocation for marketing campaigns.
Decided to increase social media spend by 20%.

Action items:
- John: Create budget proposal by Friday
- Sarah: Research new ad platforms  
- Mike: Schedule follow-up meeting next week
```

## API Endpoints

For programmatic access:

```bash
# Process text
curl -X POST http://localhost:8000/api/process-text \
  -H "Content-Type: application/json" \
  -d '{"text": "Your meeting notes here", "model": "qwen2.5:3b"}' \
  --output meeting.pdf

# Process audio
curl -X POST http://localhost:8000/api/process-audio \
  -F "file=@meeting.mp3" \
  -F "model=qwen2.5:3b" \
  --output meeting.pdf
```

## Project Structure

```
meeting-to-pdf/
├── app.py                    # FastAPI server
├── services/
│   ├── ai_processor.py       # Ollama AI integration
│   ├── transcriber.py        # faster-whisper transcription
│   └── pdf_generator.py      # WeasyPrint PDF generation
├── templates/
│   └── meeting_report.html   # PDF template
├── uploads/                  # Temporary audio uploads
├── output/                   # Generated PDFs
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Configuration

### Changing the AI Model

Edit `app.py` and change the default model:

```python
DEFAULT_MODEL = "qwen2.5:7b"  # or any model you have installed
```

### Changing Whisper Model Size

Edit `services/transcriber.py`:

```python
# Options: tiny, base, small, medium, large-v2, large-v3
# Larger = more accurate but slower
DEFAULT_MODEL_SIZE = "base"
```

## Troubleshooting

### "Ollama not running"

Start Ollama in a separate terminal:
```bash
ollama serve
```

### "Model not found"

Pull the model first:
```bash
ollama pull qwen2.5:3b
```

### WeasyPrint Installation Issues

**Windows:**
1. Install GTK+ runtime from https://github.com/nicm/weasyprint/releases
2. Add GTK+ to your PATH

**Linux (Ubuntu/Debian):**
```bash
sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev
```

**Mac:**
```bash
brew install pango gdk-pixbuf libffi
```

### Slow Processing

- Use a smaller model: `ollama pull qwen2.5:1.5b`
- Use a smaller Whisper model: change to `tiny` in transcriber.py
- Ensure GPU acceleration is enabled (NVIDIA CUDA or Apple Metal)

## License

MIT License
