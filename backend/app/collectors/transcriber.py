import logging
import tempfile
import os
import yt_dlp

logger = logging.getLogger(__name__)

TRANSCRIBE_MIN_DURATION = 600  # 10 minutos em segundos

class VideoTranscriber:
    def should_transcribe(self, duration_seconds: int) -> bool:
        return duration_seconds >= TRANSCRIBE_MIN_DURATION

    def get_transcript(self, video_id: str) -> str | None:
        url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            "skip_download": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["pt", "pt-BR"],
            "subtitlesformat": "vtt",
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                duration = info.get("duration", 0)

                if not self.should_transcribe(duration):
                    return None

                captions = info.get("automatic_captions", {})
                if captions.get("pt"):
                    return f"[legenda disponível: {captions['pt'][0]['url']}]"
                if captions.get("pt-BR"):
                    return f"[legenda disponível: {captions['pt-BR'][0]['url']}]"

                return self._transcribe_with_whisper(url)

        except Exception as e:
            logger.error(f"Erro ao transcrever vídeo {video_id}: {e}")
            return None

    def _transcribe_with_whisper(self, url: str) -> str | None:
        """Fallback: baixa áudio e usa Whisper para transcrever."""
        try:
            import whisper
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path = os.path.join(tmpdir, "audio.mp3")
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": audio_path,
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3"
                    }],
                    "quiet": True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                model = whisper.load_model("base")
                result = model.transcribe(audio_path, language="pt")
                return result["text"]
        except Exception as e:
            logger.error(f"Whisper falhou: {e}")
            return None
