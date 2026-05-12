from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Character(BaseModel):
    id: str = Field(..., description="角色唯一标识")
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")

class CharacterCreate(BaseModel):
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")

class Dialogue(BaseModel):
    speaker: str = Field(..., description="说话者")
    text: str = Field(..., description="对话文本")
    position: Optional[str] = Field("center", description="显示位置")

class Narration(BaseModel):
    text: str = Field(..., description="旁白文本")
    position: Optional[str] = Field("top", description="显示位置")

class Action(BaseModel):
    description: str = Field(..., description="动作描述")
    position: Optional[str] = Field("bottom", description="显示位置")

class Script(BaseModel):
    id: str = Field(..., description="剧本唯一标识")
    project_id: str = Field(..., description="所属项目ID")
    dialogues: List[Dialogue] = Field(..., description="对话列表")
    narrations: List[Narration] = Field(..., description="旁白列表")
    actions: List[Action] = Field(..., description="动作列表")
    characters: List[str] = Field(..., description="角色名称列表")
    created_at: datetime = Field(default_factory=datetime.now)

class Project(BaseModel):
    id: str = Field(..., description="项目唯一标识")
    title: str = Field(..., description="项目标题")
    description: Optional[str] = Field(None, description="项目描述")
    script: Optional[Script] = Field(None, description="关联的剧本")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ScriptRequest(BaseModel):
    raw_text: str = Field(..., description="原始剧本文本")

class ScriptResponse(BaseModel):
    dialogues: List[Dialogue] = Field(..., description="对话列表")
    narrations: List[Narration] = Field(..., description="旁白列表")
    actions: List[Action] = Field(..., description="动作列表")
    characters: List[dict] = Field(..., description="角色列表（包含名称和描述）")

class Shot(BaseModel):
    shot_id: int = Field(..., description="镜头编号")
    scene_type: str = Field(..., description="景别（全景、中景、特写等）")
    duration: float = Field(..., description="镜头时长（秒）")
    camera_movement: Optional[str] = Field(None, description="镜头运动（推、拉、摇、移等）")
    visual_description: str = Field(..., description="画面描述")
    character_emotion: Optional[str] = Field(None, description="角色情绪")
    dialogue: Optional[str] = Field("", description="该镜头中的对白")
    narration: Optional[str] = Field("", description="该镜头中的旁白")
    image_url: Optional[str] = Field(None, description="生成的图片URL")

class StoryboardResponse(BaseModel):
    shots: List[Shot] = Field(..., description="分镜列表")

class StoryboardRequest(BaseModel):
    script: ScriptResponse = Field(..., description="结构化剧本")

class ShotUpdateRequest(BaseModel):
    scene_type: Optional[str] = Field(None, description="景别")
    duration: Optional[float] = Field(None, description="镜头时长")
    camera_movement: Optional[str] = Field(None, description="镜头运动")
    visual_description: Optional[str] = Field(None, description="画面描述")
    character_emotion: Optional[str] = Field(None, description="角色情绪")
    dialogue: Optional[str] = Field(None, description="对白")
    narration: Optional[str] = Field(None, description="旁白")