import os
import requests
import json
import subprocess
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

@dataclass
class DialogueLine:
    speaker: str
    text: str
    start_time: float = 0
    end_time: float = 0

@dataclass
class VoiceConfig:
    voice_id: str = "default"
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0

class VoiceAgent:
    def __init__(self):
        self.fish_audio_api_key = os.getenv("FISH_AUDIO_API_KEY")
        self.fish_audio_api_url = os.getenv("FISH_AUDIO_API_URL", "https://api.fish.audio/v1/tts")
        self.minimax_api_key = os.getenv("MINIMAX_API_KEY")
        self.minimax_api_url = os.getenv("MINIMAX_API_URL", "https://api.minimax.chat/v1/t2a_v2")
        self.minimax_group_id = os.getenv("MINIMAX_GROUP_ID")
        self.default_tts_provider = os.getenv("TTS_PROVIDER", "fish_audio")

        self.voice_presets = {
            "林风": "young_male_chinese_1",
            "壮汉": "middle_male_chinese_1",
            "旁白": "female_chinese_1",
            "default_male": "male_chinese_1",
            "default_female": "female_chinese_1"
        }

    def generate_speech(
        self,
        text: str,
        voice_id: str = "default",
        speed: float = 1.0,
        provider: Optional[str] = None
    ) -> bytes:
        provider = provider or self.default_tts_provider

        if provider == "fish_audio":
            return self._generate_fish_audio(text, voice_id, speed)
        elif provider == "minimax":
            return self._generate_minimax(text, voice_id, speed)
        else:
            return self._generate_fish_audio(text, voice_id, speed)

    def _generate_fish_audio(
        self,
        text: str,
        voice_id: str,
        speed: float
    ) -> bytes:
        if not self.fish_audio_api_key:
            return self._generate_mock_audio(text)

        headers = {
            "Authorization": f"Bearer {self.fish_audio_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": voice_id,
            "text": text,
            "speed": speed
        }

        try:
            response = requests.post(
                self.fish_audio_api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Fish Audio API failed: {e}")
            return self._generate_mock_audio(text)

    def _generate_minimax(
        self,
        text: str,
        voice_id: str,
        speed: float
    ) -> bytes:
        if not self.minimax_api_key or not self.minimax_group_id:
            return self._generate_mock_audio(text)

        headers = {
            "Authorization": f"Bearer {self.minimax_api_key}",
            "Content-Type": "application/json"
        }

        voice_id_map = {
            "male_chinese_1": "male_qn_qingse",
            "female_chinese_1": "female_shaonang_qianjing",
            "young_male_chinese_1": "male_qn_qingse",
            "middle_male_chinese_1": "male_qn_qingse"
        }

        mapped_voice = voice_id_map.get(voice_id, "female_shaonang_qianjing")

        payload = {
            "model": "speech-02",
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": mapped_voice,
                "speed": speed,
                "pitch": 0,
                "volume": 0,
                "output_format": "mp3"
            },
            "request_id": f"voice_{datetime.now().timestamp()}"
        }

        try:
            response = requests.post(
                f"{self.minimax_api_url}?GroupId={self.minimax_group_id}",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()

            if result.get("data", {}).get("audio_file"):
                audio_url = result["data"]["audio_file"]
                audio_response = requests.get(audio_url, timeout=60)
                return audio_response.content

            return self._generate_mock_audio(text)

        except Exception as e:
            print(f"Minimax API failed: {e}")
            return self._generate_mock_audio(text)

    def _generate_mock_audio(self, text: str) -> bytes:
        return b"MOCK_AUDIO_DATA"

    def generate_dialogue_audio(
        self,
        dialogues: List[Dict],
        output_dir: str,
        progress_callback=None
    ) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)

        audio_files = {}
        current_time = 0.0
        total = len(dialogues)

        for i, dialogue in enumerate(dialogues):
            speaker = dialogue.get("speaker", "unknown")
            text = dialogue.get("text", "")

            if not text:
                continue

            voice_id = self._get_voice_for_speaker(speaker)

            audio_data = self.generate_speech(
                text=text,
                voice_id=voice_id,
                speed=1.0
            )

            audio_filename = f"{speaker}_{i+1}.mp3"
            audio_path = os.path.join(output_dir, audio_filename)

            with open(audio_path, 'wb') as f:
                f.write(audio_data)

            duration = self._estimate_duration(text)

            audio_files[f"{speaker}_{i+1}"] = {
                "path": audio_path,
                "start_time": current_time,
                "end_time": current_time + duration,
                "speaker": speaker,
                "text": text
            }

            current_time += duration + 0.3

            if progress_callback:
                progress = int((i + 1) / total * 100)
                progress_callback(speaker, progress)

        return audio_files

    def _get_voice_for_speaker(self, speaker: str) -> str:
        for name_key, voice_id in self.voice_presets.items():
            if name_key in speaker:
                return voice_id
        return "default_male" if "男" not in speaker else "default_female"

    def _estimate_duration(self, text: str) -> float:
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return (chinese_chars * 0.3 + other_chars * 0.5)

    def generate_srt(
        self,
        dialogues: List[Dict],
        narrations: List[Dict] = None,
        output_path: str = None
    ) -> str:
        srt_lines = []
        index = 1
        current_time = 0.0

        all_items = []
        for d in dialogues:
            all_items.append({
                "type": "dialogue",
                "speaker": d.get("speaker", ""),
                "text": d.get("text", ""),
                "start": current_time
            })
            current_time += self._estimate_duration(d.get("text", "")) + 0.5

        if narrations:
            for n in narrations:
                all_items.append({
                    "type": "narration",
                    "speaker": "",
                    "text": n.get("text", ""),
                    "start": current_time
                })
                current_time += self._estimate_duration(n.get("text", "")) + 0.3

        for item in all_items:
            start_time = self._format_srt_time(item["start"])
            duration = self._estimate_duration(item["text"])
            end_time = self._format_srt_time(item["start"] + duration)

            if item["type"] == "dialogue":
                line_text = f"{item['speaker']}：{item['text']}"
            else:
                line_text = item["text"]

            srt_lines.append(f"{index}")
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(line_text)
            srt_lines.append("")

            index += 1

        srt_content = "\n".join(srt_lines)

        if output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)

        return srt_content

    def _format_srt_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    def concatenate_audio(
        self,
        audio_files: Dict[str, Dict],
        output_path: str
    ) -> str:
        if not audio_files:
            return ""

        list_file = os.path.join(os.path.dirname(output_path), "audio_list.txt")

        sorted_files = sorted(audio_files.items(), key=lambda x: x[1]["start_time"])

        with open(list_file, 'w', encoding='utf-8') as f:
            for filename, info in sorted_files:
                abs_path = os.path.abspath(info["path"])
                f.write(f"file '{abs_path}'\n")

        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            '-y', output_path
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except Exception as e:
            print(f"Audio concatenation failed: {e}")
            return sorted_files[0][1]["path"] if sorted_files else ""

    def generate_full_audio(
        self,
        dialogues: List[Dict],
        narrations: List[Dict] = None,
        output_dir: str = "output/audio"
    ) -> Dict:
        os.makedirs(output_dir, exist_ok=True)

        dialogue_files = self.generate_dialogue_audio(
            dialogues=dialogues,
            output_dir=output_dir
        )

        combined_audio = os.path.join(output_dir, "combined.mp3")
        self.concatenate_audio(dialogue_files, combined_audio)

        srt_path = os.path.join(output_dir, "subtitles.srt")
        self.generate_srt(
            dialogues=dialogues,
            narrations=narrations,
            output_path=srt_path
        )

        return {
            "combined_audio": combined_audio,
            "dialogue_files": [f["path"] for f in dialogue_files.values()],
            "srt_path": srt_path,
            "duration": sum(self._estimate_duration(d.get("text", "")) for d in dialogues)
        }