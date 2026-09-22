import os
import torch
import torchaudio

class AudioDuration:
    """
    ComfyUI Node to extract duration from an AUDIO input or audio file path.
    Outputs duration in seconds (INT/FLOAT) and minutes (INT/FLOAT).
    Matches the exact schema used in ComfyUI MiniMax-H3 workflows.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {},
            "optional": {
                "audio": ("AUDIO",),
                "audio_path": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("INT", "FLOAT", "INT", "FLOAT", "STRING")
    RETURN_NAMES = ("seconds_int", "seconds_float", "minutes_int", "minutes_float", "temp_wav_path")
    FUNCTION = "get_duration"
    CATEGORY = "audio"

    def get_duration(self, audio=None, audio_path=""):
        seconds = 0.0
        temp_wav_path = ""

        if audio is not None and isinstance(audio, dict):
            waveform = audio.get("waveform")
            sample_rate = audio.get("sample_rate", 44100)
            if waveform is not None:
                # waveform shape is usually [batch, channels, samples] or [channels, samples]
                num_samples = waveform.shape[-1]
                seconds = float(num_samples) / float(sample_rate)

        elif audio_path and os.path.exists(audio_path):
            try:
                info = torchaudio.info(audio_path)
                seconds = float(info.num_frames) / float(info.sample_rate)
                temp_wav_path = audio_path
            except Exception as e:
                print(f"[AudioDuration] Error reading audio_path: {e}")
                seconds = 0.0

        seconds_float = float(seconds)
        seconds_int = int(round(seconds))
        minutes_float = float(seconds / 60.0)
        minutes_int = int(seconds // 60)

        return (seconds_int, seconds_float, minutes_int, minutes_float, temp_wav_path)

NODE_CLASS_MAPPINGS = {
    "Audio Duration": AudioDuration
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Audio Duration": "Audio Duration"
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

