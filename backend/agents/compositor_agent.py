import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from build_video import VideoBuilder, ShotConfig, AudioConfig, SubtitleConfig

@dataclass
class CompositorConfig:
    project_id: str
    shots: List[Dict]
    audio_path: Optional[str] = None
    srt_path: Optional[str] = None
    music_path: Optional[str] = None
    music_volume: float = 0.3
    output_dir: str = "output"
    output_filename: str = "final.mp4"
    resolution: tuple = (1920, 1080)
    fps: int = 24

class CompositorAgent:
    def __init__(self):
        self.output_dir = "output"

    def compose_video(
        self,
        project_id: str,
        shots: List[Dict],
        audio_path: Optional[str] = None,
        srt_path: Optional[str] = None,
        music_path: Optional[str] = None,
        music_volume: float = 0.3,
        output_filename: str = "final.mp4",
        progress_callback=None
    ) -> str:
        output_dir = os.path.join(self.output_dir, project_id)
        os.makedirs(output_dir, exist_ok=True)

        video_builder = VideoBuilder(output_dir)

        shot_configs = []
        for shot in shots:
            image_path = self._get_shot_image_path(shot, project_id)

            camera_movement = shot.get("camera_movement")
            zoom_factor = 1.0
            if camera_movement:
                zoom_factor = self._get_zoom_from_movement(camera_movement)

            transition = shot.get("transition", "none")
            transition_duration = shot.get("transition_duration", 0.5)

            shot_config = ShotConfig(
                shot_id=shot.get("shot_id", 1),
                image_path=image_path,
                duration=shot.get("duration", 2.0),
                camera_movement=camera_movement,
                zoom_factor=zoom_factor,
                transition=transition,
                transition_duration=transition_duration
            )
            shot_configs.append(shot_config)

        audio_config = None
        if audio_path and os.path.exists(audio_path):
            audio_config = AudioConfig(
                voice_path=audio_path,
                music_path=music_path,
                music_volume=music_volume,
                voice_volume=1.0
            )

        subtitle_config = None
        if srt_path and os.path.exists(srt_path):
            subtitle_config = SubtitleConfig(
                srt_path=srt_path,
                font_size=48,
                font_color="white",
                position="bottom",
                stroke_color="black",
                stroke_width=2
            )

        if progress_callback:
            progress_callback(0, "正在生成视频片段...")

        final_video = video_builder.build_final_video(
            shots=shot_configs,
            audio_config=audio_config,
            subtitle_config=subtitle_config,
            output_filename=output_filename
        )

        if progress_callback:
            progress_callback(100, "视频合成完成")

        return final_video

    def _get_shot_image_path(self, shot: Dict, project_id: str) -> str:
        image_url = shot.get("image_url", "")

        if image_url and os.path.exists(image_url.lstrip("/")):
            return image_url.lstrip("/")

        if image_url and image_url.startswith("/"):
            return image_url.lstrip("/")

        shot_id = shot.get("shot_id", 1)
        default_path = f"static/images/{project_id}/{shot_id}.png"
        if os.path.exists(default_path):
            return default_path

        placeholder = "static/placeholder.png"
        if os.path.exists(placeholder):
            return placeholder

        return "static/placeholder.png"

    def _get_zoom_from_movement(self, movement: str) -> float:
        movement_map = {
            "推近": 1.3,
            "拉远": 0.7,
            "缓慢推近": 1.15,
            "缓慢拉远": 0.85,
            "zoom_in": 1.3,
            "zoom_out": 0.7,
            "slow_zoom_in": 1.15,
            "slow_zoom_out": 0.85
        }
        return movement_map.get(movement, 1.0)

    def compose_with_config(self, config: CompositorConfig, progress_callback=None) -> str:
        return self.compose_video(
            project_id=config.project_id,
            shots=config.shots,
            audio_path=config.audio_path,
            srt_path=config.srt_path,
            music_path=config.music_path,
            music_volume=config.music_volume,
            output_filename=config.output_filename,
            progress_callback=progress_callback
        )

    def compose_from_project(
        self,
        project_dir: str,
        output_filename: str = "final.mp4",
        progress_callback=None
    ) -> str:
        config_path = os.path.join(project_dir, "config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        project_id = config_data.get("project_id", os.path.basename(project_dir))

        shots = config_data.get("shots", [])
        audio_path = config_data.get("audio_path")
        srt_path = config_data.get("srt_path")
        music_path = config_data.get("music_path")
        music_volume = config_data.get("music_volume", 0.3)

        if audio_path and not os.path.isabs(audio_path):
            audio_path = os.path.join(project_dir, audio_path)
        if srt_path and not os.path.isabs(srt_path):
            srt_path = os.path.join(project_dir, srt_path)
        if music_path and not os.path.isabs(music_path):
            music_path = os.path.join(project_dir, music_path)

        return self.compose_video(
            project_id=project_id,
            shots=shots,
            audio_path=audio_path if audio_path and os.path.exists(audio_path) else None,
            srt_path=srt_path if srt_path and os.path.exists(srt_path) else None,
            music_path=music_path if music_path and os.path.exists(music_path) else None,
            music_volume=music_volume,
            output_filename=output_filename,
            progress_callback=progress_callback
        )

    def generate_preview(
        self,
        project_id: str,
        shot: Dict,
        output_path: Optional[str] = None
    ) -> str:
        output_dir = os.path.join(self.output_dir, project_id, "previews")
        os.makedirs(output_dir, exist_ok=True)

        if output_path is None:
            shot_id = shot.get("shot_id", "preview")
            output_path = os.path.join(output_dir, f"preview_{shot_id}.mp4")

        video_builder = VideoBuilder(output_dir)

        image_path = self._get_shot_image_path(shot, project_id)

        shot_config = ShotConfig(
            shot_id=shot.get("shot_id", 0),
            image_path=image_path,
            duration=shot.get("duration", 3.0),
            camera_movement=shot.get("camera_movement"),
            zoom_factor=self._get_zoom_from_movement(shot.get("camera_movement", "")) if shot.get("camera_movement") else 1.0
        )

        video_builder.build_shot_video(shot_config, output_path)

        return output_path

    def save_composition_config(
        self,
        project_id: str,
        shots: List[Dict],
        audio_path: Optional[str] = None,
        srt_path: Optional[str] = None,
        music_path: Optional[str] = None,
        music_volume: float = 0.3
    ) -> str:
        output_dir = os.path.join(self.output_dir, project_id)
        os.makedirs(output_dir, exist_ok=True)

        config = {
            "project_id": project_id,
            "shots": shots,
            "audio_path": audio_path,
            "srt_path": srt_path,
            "music_path": music_path,
            "music_volume": music_volume
        }

        config_path = os.path.join(output_dir, "config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        return config_path