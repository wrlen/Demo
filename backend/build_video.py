import subprocess
import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ShotConfig:
    shot_id: int
    image_path: str
    duration: float
    camera_movement: Optional[str] = None
    zoom_factor: float = 1.0
    pan_x: float = 0
    pan_y: float = 0
    transition: str = "none"
    transition_duration: float = 0.5

@dataclass
class AudioConfig:
    voice_path: Optional[str] = None
    music_path: Optional[str] = None
    music_volume: float = 0.3
    voice_volume: float = 1.0
    fade_in: float = 0
    fade_out: float = 0

@dataclass
class SubtitleConfig:
    srt_path: str
    font_size: int = 48
    font_color: str = "white"
    position: str = "bottom"
    stroke_color: str = "black"
    stroke_width: float = 2

class VideoBuilder:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.temp_dir = os.path.join(output_dir, "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

    def build_shot_video(
        self,
        shot: ShotConfig,
        output_path: str,
        resolution: tuple = (1920, 1080),
        fps: int = 24
    ) -> str:
        if not os.path.exists(shot.image_path):
            raise FileNotFoundError(f"Image not found: {shot.image_path}")

        filter_complex = self._build_camera_filter(shot, resolution)

        cmd = [
            'ffmpeg', '-loop', '1',
            '-i', shot.image_path,
            '-t', str(shot.duration),
            '-r', str(fps),
            '-vf', filter_complex,
            '-pix_fmt', 'yuv420p',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '18',
            '-y', output_path
        ]

        subprocess.run(cmd, capture_output=True)
        return output_path

    def _build_camera_filter(self, shot: ShotConfig, resolution: tuple) -> str:
        w, h = resolution
        filters = []

        zoom = shot.zoom_factor
        if shot.camera_movement:
            if shot.camera_movement in ["推近", "zoom_in"]:
                zoom = shot.zoom_factor * 1.3
            elif shot.camera_movement in ["拉远", "zoom_out"]:
                zoom = shot.zoom_factor * 0.7
            elif shot.camera_movement in ["缓慢推近", "slow_zoom_in"]:
                zoom = shot.zoom_factor * 1.15
            elif shot.camera_movement in ["缓慢拉远", "slow_zoom_out"]:
                zoom = shot.zoom_factor * 0.85

        if shot.camera_movement in ["左摇", "pan_left"]:
            pan_x = -0.2
        elif shot.camera_movement in ["右摇", "pan_right"]:
            pan_x = 0.2
        elif shot.camera_movement in ["上摇", "tilt_up"]:
            pan_y = -0.15
        elif shot.camera_movement in ["下摇", "tilt_down"]:
            pan_y = 0.15
        else:
            pan_x = shot.pan_x
            pan_y = shot.pan_y

        zoom = max(1.0, min(zoom, 3.0))

        if zoom != 1.0 or pan_x != 0 or pan_y != 0:
            scale_w = int(w * zoom)
            scale_h = int(h * zoom)
            filters.append(f"scale={scale_w}:{scale_h}")

            if pan_x != 0 or pan_y != 0:
                offset_x = int(scale_w * pan_x)
                offset_y = int(scale_h * pan_y)
                max_x = scale_w - w
                max_y = scale_h - h
                crop_x = max(0, min(max_x, offset_x + max_x // 2))
                crop_y = max(0, min(max_y, offset_y + max_y // 2))
                filters.append(f"crop={w}:{h}:{crop_x}:{crop_y}")
            else:
                filters.append(f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2")

        if not filters:
            filters.append(f"scale={w}:{h}")

        return ",".join(filters)

    def add_transition(
        self,
        clip1_path: str,
        clip2_path: str,
        output_path: str,
        transition_type: str = "fade",
        duration: float = 0.5
    ) -> str:
        if transition_type == "fade":
            cmd = [
                'ffmpeg',
                '-i', clip1_path,
                '-i', clip2_path,
                '-filter_complex',
                f'[0:v]fade=t=out:st={duration}:d={duration}[v0];[1:v]fade=t=in:st=0:d={duration}[v1];[v0][v1]concat=n=2:v=1:a=0[out]',
                '-map', '[out]',
                '-y', output_path
            ]
        elif transition_type == "dissolve":
            cmd = [
                'ffmpeg',
                '-i', clip1_path,
                '-i', clip2_path,
                '-filter_complex',
                f'[0:v][1:v]blend=all_opacity=0.5[blended];[blended]concat=n=2:v=1:a=0[out]',
                '-map', '[out]',
                '-y', output_path
            ]
        elif transition_type == "wipe":
            cmd = [
                'ffmpeg',
                '-i', clip1_path,
                '-i', clip2_path,
                '-filter_complex',
                f'[0:v][1:v]libavfilter/tblend=all_mode=addition[blended];[blended]concat=n=2:v=1:a=0[out]',
                '-map', '[out]',
                '-y', output_path
            ]
        else:
            return clip1_path

        subprocess.run(cmd, capture_output=True)
        return output_path

    def concatenate_videos(
        self,
        video_paths: List[str],
        output_path: str
    ) -> str:
        concat_list_path = os.path.join(self.temp_dir, "concat_list.txt")

        with open(concat_list_path, 'w') as f:
            for path in video_paths:
                abs_path = os.path.abspath(path)
                f.write(f"file '{abs_path}'\n")

        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_list_path,
            '-c', 'copy',
            '-y', output_path
        ]

        subprocess.run(cmd, capture_output=True)
        return output_path

    def burn_subtitles(
        self,
        video_path: str,
        subtitle_config: SubtitleConfig,
        output_path: str
    ) -> str:
        if not os.path.exists(subtitle_config.srt_path):
            return video_path

        position_map = {
            "bottom": "y=h-th-20",
            "top": "y=20",
            "center": "y=(h-th)/2"
        }
        pos = position_map.get(subtitle_config.position, position_map["bottom"])

        filter_complex = (
            f"subtitles='{subtitle_config.srt_path}':"
            f"force_style='FontSize={subtitle_config.font_size},"
            f"PrimaryColour=&H{self._color_to_hex(subtitle_config.font_color)},"
            f"OutlineColour=&H{self._color_to_hex(subtitle_config.stroke_color)},"
            f"Outline={subtitle_config.stroke_width},"
            f"Alignment=2,"
            f"MarginV=20'"
        )

        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', filter_complex,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '18',
            '-y', output_path
        ]

        subprocess.run(cmd, capture_output=True)
        return output_path

    def _color_to_hex(self, color: str) -> str:
        color_map = {
            "white": "FFFFFF",
            "black": "000000",
            "yellow": "FFFF00",
            "red": "FF0000",
            "green": "00FF00",
            "blue": "0000FF"
        }
        return color_map.get(color.lower(), "FFFFFF")

    def mix_audio(
        self,
        video_path: str,
        audio_config: AudioConfig,
        output_path: str
    ) -> str:
        audio_filters = []
        audio_inputs = ['-i', video_path]
        filter_complex_parts = []
        mix_inputs = []

        if audio_config.voice_path and os.path.exists(audio_config.voice_path):
            audio_inputs.extend(['-i', audio_config.voice_path])
            mix_inputs.append(1)
            if audio_config.voice_volume != 1.0:
                db = 20 * (audio_config.voice_volume - 1)
                audio_filters.append(f"[1:a]volume={audio_config.voice_volume}dB,apad[voice]")

        if audio_config.music_path and os.path.exists(audio_config.music_path):
            audio_inputs.extend(['-i', audio_config.music_path])
            mix_inputs.append(2)
            audio_filters.append(f"[2:a]volume={audio_config.music_volume}[music]")

        if audio_filters:
            filter_complex = ";".join(audio_filters)
            if len(mix_inputs) > 1:
                filter_complex += f";[voice][music]amix=inputs=2:duration=first[outa]"
                audio_map = ['-map', '[outa]']
            else:
                audio_map = ['-map', '[voice]']
        else:
            audio_map = ['-map', '1:a'] if len(audio_inputs) > 2 else []

        if audio_filters:
            cmd = ['ffmpeg'] + audio_inputs + [
                '-filter_complex', filter_complex,
                '-map', '0:v'
            ] + audio_map + [
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]
        else:
            return video_path

        subprocess.run(cmd, capture_output=True)
        return output_path

    def build_final_video(
        self,
        shots: List[ShotConfig],
        audio_config: Optional[AudioConfig] = None,
        subtitle_config: Optional[SubtitleConfig] = None,
        output_filename: str = "final.mp4"
    ) -> str:
        temp_clips = []
        final_output = os.path.join(self.output_dir, output_filename)

        for i, shot in enumerate(shots):
            clip_path = os.path.join(self.temp_dir, f"shot_{shot.shot_id}.mp4")

            if shot.transition != "none" and i > 0:
                prev_clip = temp_clips[-1]
                clip_with_trans = os.path.join(self.temp_dir, f"shot_{shot.shot_id}_trans.mp4")
                self.add_transition(
                    prev_clip, clip_path,
                    clip_with_trans,
                    transition_type=shot.transition,
                    duration=shot.transition_duration
                )
                temp_clips[-1] = clip_with_trans
                clip_path = clip_with_trans

            self.build_shot_video(shot, clip_path)
            temp_clips.append(clip_path)

        concat_output = os.path.join(self.temp_dir, "concat_output.mp4")
        self.concatenate_videos(temp_clips, concat_output)

        current_video = concat_output

        if subtitle_config:
            with_subtitles = os.path.join(self.temp_dir, "with_subtitles.mp4")
            current_video = self.burn_subtitles(current_video, subtitle_config, with_subtitles)

        if audio_config:
            with_audio = os.path.join(self.temp_dir, "with_audio.mp4")
            current_video = self.mix_audio(current_video, audio_config, with_audio)

        if os.path.exists(current_video):
            import shutil
            shutil.copy(current_video, final_output)
            return final_output

        return current_video

def load_config(config_path: str) -> Dict:
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_from_config(config_path: str, output_dir: str) -> str:
    config = load_config(config_path)

    shots = [
        ShotConfig(
            shot_id=s["shot_id"],
            image_path=s["image_path"],
            duration=s["duration"],
            camera_movement=s.get("camera_movement"),
            zoom_factor=s.get("zoom_factor", 1.0),
            transition=s.get("transition", "none"),
            transition_duration=s.get("transition_duration", 0.5)
        )
        for s in config.get("shots", [])
    ]

    audio_config = None
    if config.get("audio"):
        audio_config = AudioConfig(
            voice_path=config["audio"].get("voice_path"),
            music_path=config["audio"].get("music_path"),
            music_volume=config["audio"].get("music_volume", 0.3),
            voice_volume=config["audio"].get("voice_volume", 1.0)
        )

    subtitle_config = None
    if config.get("subtitles"):
        subtitle_config = SubtitleConfig(
            srt_path=config["subtitles"]["srt_path"],
            font_size=config["subtitles"].get("font_size", 48),
            font_color=config["subtitles"].get("font_color", "white"),
            position=config["subtitles"].get("position", "bottom")
        )

    builder = VideoBuilder(output_dir)
    return builder.build_final_video(
        shots=shots,
        audio_config=audio_config,
        subtitle_config=subtitle_config,
        output_filename=config.get("output_filename", "final.mp4")
    )

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python build_video.py <config_path> <output_dir>")
        sys.exit(1)

    config_path = sys.argv[1]
    output_dir = sys.argv[2]

    result = build_from_config(config_path, output_dir)
    print(f"Video built successfully: {result}")