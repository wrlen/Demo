import os
import requests
import base64
from io import BytesIO
from typing import List, Optional
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

class ArtistAgent:
    def __init__(self):
        self.api_key = os.getenv("STABLE_DIFFUSION_API_KEY")
        self.api_base_url = os.getenv("STABLE_DIFFUSION_API_URL", "http://localhost:7860")
        self.default_model = os.getenv("STABLE_DIFFUSION_MODEL", "stable-diffusion-xl-base-1.0")

    def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        cfg_scale: float = 7.5,
        seed: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        url = f"{self.api_base_url}/sdapi/v1/txt2img"

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or self._get_default_negative(),
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "model": model or self.default_model,
        }

        if seed is not None:
            payload["seed"] = seed

        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()

            result = response.json()
            if "images" in result and len(result["images"]) > 0:
                return result["images"][0]
            else:
                raise Exception("No image in response")

        except requests.exceptions.ConnectionError:
            return self._generate_placeholder_image(prompt)
        except Exception as e:
            print(f"Image generation failed: {e}")
            return self._generate_placeholder_image(prompt)

    def _get_default_negative(self) -> str:
        return (
            "low quality, worst quality, blurry, deformed, disfigured, "
            "mutated, ugly, bad anatomy, bad proportions, extra limbs, "
            "missing limbs, floating limbs, disconnected limbs, mutated hands, "
            "extra fingers, missing fingers, wrong hands, blurry, watermark, "
            "text, logo, signature"
        )

    def _generate_placeholder_image(self, prompt: str) -> str:
        img = Image.new('RGB', (512, 512), color=(50, 50, 50))
        return img

    def save_image(self, image_data: str, output_path: str) -> str:
        if image_data.startswith("data:"):
            image_data = image_data.split(",")[1]

        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path)
        return output_path

    def generate_character_reference(
        self,
        character_name: str,
        description: str,
        view_type: str,
        output_dir: str
    ) -> str:
        prompts = {
            "front": (
                f"{character_name}, {description}, "
                "full body shot, front view, standing pose, facing camera, "
                "white background, realistic photography style, "
                "cinematic lighting, 8k ultra sharp, highly detailed"
            ),
            "side": (
                f"{character_name}, {description}, "
                "full body shot, side view, standing pose, "
                "white background, realistic photography style, "
                "cinematic lighting, 8k ultra sharp, highly detailed"
            ),
            "back": (
                f"{character_name}, {description}, "
                "full body shot, back view, standing pose, "
                "white background, realistic photography style, "
                "cinematic lighting, 8k ultra sharp, highly detailed"
            )
        }

        negative_prompt = (
            "low quality, worst quality, blurry, deformed, disfigured, "
            "multiple views, side views, back view in prompt, "
            "cartoon, anime style, illustration"
        )

        prompt = prompts.get(view_type, prompts["front"])

        image_data = self.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=1024,
            height=1024,
            steps=35,
            cfg_scale=7.5
        )

        output_path = os.path.join(output_dir, f"{character_name}_{view_type}.png")

        if isinstance(image_data, str) and not image_data.startswith("data:"):
            return image_data

        return self.save_image(image_data, output_path)

    def generate_shot_image(
        self,
        visual_description: str,
        character_prompts: Optional[List[str]] = None,
        scene_type: Optional[str] = None,
        output_dir: str = "static/images",
        shot_id: int = 1,
        project_id: str = "default"
    ) -> str:
        prompt = self._build_shot_prompt(
            visual_description,
            character_prompts,
            scene_type
        )

        width, height = self._get_resolution(scene_type)

        image_data = self.generate_image(
            prompt=prompt,
            negative_prompt=self._get_shot_negative(),
            width=width,
            height=height,
            steps=30,
            cfg_scale=7.5
        )

        project_dir = os.path.join(output_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)
        output_path = os.path.join(project_dir, f"{shot_id}.png")

        if isinstance(image_data, str) and not image_data.startswith("data:"):
            return image_data

        return self.save_image(image_data, output_path)

    def _build_shot_prompt(
        self,
        visual_description: str,
        character_prompts: Optional[List[str]] = None,
        scene_type: Optional[str] = None
    ) -> str:
        scene_prefix = ""
        if scene_type:
            scene_map = {
                "全景": "wide shot, establishing shot,",
                "中景": "medium shot,",
                "特写": "close-up shot, detailed,",
                "近景": "close-up,",
                "远景": "long shot, establishing view,",
                "大特写": "extreme close-up, detailed,"
            }
            scene_prefix = scene_map.get(scene_type, "")

        character_prompt = ""
        if character_prompts:
            character_prompt = "Characters: " + ", ".join(character_prompts) + "."

        full_prompt = (
            f"{scene_prefix} {visual_description}. "
            f"{character_prompt} "
            "anime style, manga aesthetic, cel shading, "
            "high quality illustration, vibrant colors, "
            "cinematic composition, dramatic lighting, "
            "8k resolution, highly detailed"
        )

        return full_prompt

    def _get_shot_negative(self) -> str:
        return (
            "low quality, worst quality, blurry, deformed, disfigured, "
            "mutated, ugly, bad anatomy, bad proportions, extra limbs, "
            "missing limbs, floating limbs, disconnected limbs, "
            "mutated hands, extra fingers, missing fingers, "
            "realistic, photorealistic, photograph, 3d render, "
            "watermark, text, logo, signature"
        )

    def _get_resolution(self, scene_type: Optional[str]) -> tuple:
        resolution_map = {
            "全景": (1920, 1080),
            "远景": (1920, 1080),
            "中景": (1024, 1024),
            "近景": (768, 1024),
            "特写": (768, 1024),
            "大特写": (512, 768)
        }
        return resolution_map.get(scene_type or "中景", (1024, 1024))

    def batch_generate(
        self,
        shots_data: List[dict],
        output_dir: str = "static/images",
        project_id: str = "default",
        progress_callback=None
    ) -> List[dict]:
        results = []
        total = len(shots_data)

        for i, shot_data in enumerate(shots_data):
            shot_id = shot_data.get("shot_id", i + 1)
            visual_description = shot_data.get("visual_description", "")
            character_prompts = shot_data.get("character_prompts", [])
            scene_type = shot_data.get("scene_type")

            try:
                output_path = self.generate_shot_image(
                    visual_description=visual_description,
                    character_prompts=character_prompts,
                    scene_type=scene_type,
                    output_dir=output_dir,
                    shot_id=shot_id,
                    project_id=project_id
                )

                results.append({
                    "shot_id": shot_id,
                    "status": "success",
                    "image_url": f"/static/images/{project_id}/{shot_id}.png",
                    "path": output_path
                })

            except Exception as e:
                results.append({
                    "shot_id": shot_id,
                    "status": "failed",
                    "error": str(e)
                })

            if progress_callback:
                progress = int((i + 1) / total * 100)
                progress_callback(shot_id, progress)

        return results