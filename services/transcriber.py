"""Audio transcription using faster-whisper for local speech-to-text."""

import os
from pathlib import Path
from typing import Optional
from faster_whisper import WhisperModel


# Model size options: tiny, base, small, medium, large-v2, large-v3
# Larger models are more accurate but slower
DEFAULT_MODEL_SIZE = "base"


class AudioTranscriber:
    """Handles audio transcription using faster-whisper."""

    def __init__(self, model_size: str = DEFAULT_MODEL_SIZE):
        """
        Initialize the transcriber with a specific model size.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v2, large-v3)
        """
        self.model_size = model_size
        self.model = None

    def _load_model(self):
        """Lazy load the whisper model."""
        if self.model is None:
            # Use CPU if no GPU available, with int8 quantization for speed
            self.model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8"
            )

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> dict:
        """
        Transcribe an audio file to text.

        Args:
            audio_path: Path to the audio file
            language: Optional language code (e.g., 'en' for English)

        Returns:
            Dictionary with transcription results
        """
        self._load_model()

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Transcribe the audio
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True  # Voice Activity Detection for better quality
        )

        # Collect all segments
        full_text = []
        segments_list = []

        for segment in segments:
            full_text.append(segment.text.strip())
            segments_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })

        return {
            "text": " ".join(full_text),
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "segments": segments_list
        }

    async def transcribe_to_text(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> str:
        """
        Simple transcription that returns just the text.

        Args:
            audio_path: Path to the audio file
            language: Optional language code

        Returns:
            Transcribed text as a string
        """
        result = await self.transcribe(audio_path, language)
        return result["text"]


# Singleton instance for reuse
_transcriber: Optional[AudioTranscriber] = None


def get_transcriber(model_size: str = DEFAULT_MODEL_SIZE) -> AudioTranscriber:
    """Get or create a transcriber instance."""
    global _transcriber
    if _transcriber is None or _transcriber.model_size != model_size:
        _transcriber = AudioTranscriber(model_size)
    return _transcriber
