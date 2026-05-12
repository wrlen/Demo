import os
import json
import requests
from dotenv import load_dotenv
from typing import List
from models import Shot, StoryboardResponse, ScriptResponse

load_dotenv()

class DirectorAgent:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.api_base_url = os.getenv("API_BASE_URL", "https://api.example.com/v1/chat/completions")
        self.model_name = os.getenv("MODEL_NAME", "gpt-4")

    def _call_llm(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        system_prompt = """你是一位专业的漫剧导演。请根据编剧提供的结构化剧本，生成详细的分镜头脚本。

输出格式要求：
{
  "shots": [
    {
      "shot_id": 1,
      "scene_type": "全景",
      "duration": 2.5,
      "camera_movement": "缓慢推近",
      "visual_description": "俯拍视角，林风独自站在擂台一侧...",
      "character_emotion": "紧张",
      "dialogue": "",
      "narration": ""
    }
  ]
}

说明：
- shot_id: 镜头编号，从1开始递增
- scene_type: 景别，可选值：全景、中景、特写、近景、远景、大特写
- duration: 镜头时长，单位秒，建议在1-5秒之间
- camera_movement: 镜头运动，可选值：静止、推近、拉远、左摇、右摇、上摇、下摇、移动、缓慢推近、缓慢拉远
- visual_description: 详细的画面描述，包括视角、构图、角色位置、环境等
- character_emotion: 角色情绪，如：紧张、愤怒、平静、自信、惊讶等
- dialogue: 该镜头中的人物对话，如果没有则为空字符串
- narration: 该镜头中的旁白内容，如果没有则为空字符串

请根据剧本内容，合理划分镜头，确保故事流畅。"""
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(self.api_base_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"LLM API call failed: {e}")
            return self._generate_dynamic_response(prompt)

    def _generate_dynamic_response(self, script_json: str) -> str:
        try:
            script_data = json.loads(script_json)
            dialogues = script_data.get("dialogues", [])
            narrations = script_data.get("narrations", [])
            actions = script_data.get("actions", [])
            characters = script_data.get("characters", [])
            
            shots = []
            shot_id = 1
            
            for i, narration in enumerate(narrations):
                shots.append({
                    "shot_id": shot_id,
                    "scene_type": "全景",
                    "duration": 3.0,
                    "camera_movement": "缓慢推近",
                    "visual_description": f"场景描述: {narration.get('text', '')[:30]}...",
                    "character_emotion": "",
                    "dialogue": "",
                    "narration": narration.get("text", "")
                })
                shot_id += 1
            
            for i, action in enumerate(actions):
                shots.append({
                    "shot_id": shot_id,
                    "scene_type": "中景",
                    "duration": 2.0,
                    "camera_movement": "静止",
                    "visual_description": f"动作场景: {action.get('description', '')[:30]}...",
                    "character_emotion": "动态",
                    "dialogue": "",
                    "narration": ""
                })
                shot_id += 1
            
            for i, dialogue in enumerate(dialogues):
                speaker = dialogue.get("speaker", "未知")
                text = dialogue.get("text", "")
                
                shots.append({
                    "shot_id": shot_id,
                    "scene_type": "特写",
                    "duration": max(2.0, len(text) * 0.3),
                    "camera_movement": "推近",
                    "visual_description": f"{speaker} 的面部特写，表情生动",
                    "character_emotion": self._guess_emotion(text),
                    "dialogue": text,
                    "narration": ""
                })
                shot_id += 1
            
            if not shots:
                shots = [
                    {
                        "shot_id": 1,
                        "scene_type": "全景",
                        "duration": 3.0,
                        "camera_movement": "静止",
                        "visual_description": "空场景",
                        "character_emotion": "",
                        "dialogue": "",
                        "narration": "故事开始..."
                    }
                ]
            
            return json.dumps({"shots": shots})
        except Exception as e:
            print(f"Dynamic response generation failed: {e}")
            return self._generate_fallback_json()

    def _guess_emotion(self, text: str) -> str:
        text = text.lower()
        if any(word in text for word in ["！", "愤怒", "生气", "恨", "怒"]):
            return "愤怒"
        elif any(word in text for word in ["？", "疑惑", "奇怪", "为什么"]):
            return "疑惑"
        elif any(word in text for word in ["笑", "哈哈", "开心", "高兴"]):
            return "开心"
        elif any(word in text for word in ["坚定", "决心", "一定", "要"]):
            return "坚定"
        elif any(word in text for word in ["害怕", "恐惧", "怕", "惊慌"]):
            return "害怕"
        else:
            return "平静"

    def _generate_fallback_json(self) -> str:
        return json.dumps({
            "shots": [
                {
                    "shot_id": 1,
                    "scene_type": "全景",
                    "duration": 2.0,
                    "camera_movement": "静止",
                    "visual_description": "开场场景",
                    "character_emotion": "平静",
                    "dialogue": "",
                    "narration": "故事开始..."
                },
                {
                    "shot_id": 2,
                    "scene_type": "中景",
                    "duration": 2.0,
                    "camera_movement": "推近",
                    "visual_description": "角色出现",
                    "character_emotion": "中立",
                    "dialogue": "角色：你好",
                    "narration": ""
                }
            ]
        })

    def generate_storyboard(self, script: ScriptResponse) -> StoryboardResponse:
        script_json = json.dumps({
            "dialogues": [d.dict() for d in script.dialogues],
            "narrations": [n.dict() for n in script.narrations],
            "actions": [a.dict() for a in script.actions],
            "characters": script.characters
        })
        
        llm_response = self._call_llm(script_json)
        
        try:
            data = json.loads(llm_response)
            shots = [Shot(**shot) for shot in data.get("shots", [])]
            return StoryboardResponse(shots=shots)
        except json.JSONDecodeError:
            return self._generate_fallback_response()

    def _generate_fallback_response(self) -> StoryboardResponse:
        return StoryboardResponse(
            shots=[
                Shot(
                    shot_id=1,
                    scene_type="全景",
                    duration=2.0,
                    camera_movement="静止",
                    visual_description="场景描述",
                    character_emotion="平静",
                    dialogue="",
                    narration="这是一段旁白"
                ),
                Shot(
                    shot_id=2,
                    scene_type="中景",
                    duration=2.0,
                    camera_movement="推近",
                    visual_description="角色对话场景",
                    character_emotion="中立",
                    dialogue="角色A：你好",
                    narration=""
                )
            ]
        )