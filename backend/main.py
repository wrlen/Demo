from fastapi import FastAPI, HTTPException, Form, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional, List
from uuid import uuid4
from models import Project, Script, ScriptRequest, ScriptResponse, StoryboardResponse, ShotUpdateRequest, CharacterCreate
from agents.writer_agent import WriterAgent
from agents.director_agent import DirectorAgent
from database import get_db, init_db, Project as DBProject, Shot, Character, CharacterReference, Task, TaskStatus, TaskType
from tasks import generate_images_task, regenerate_shot_task, generate_voice_task, generate_character_task
from websocket_manager import ws_manager, broadcast_progress, broadcast_task_complete, broadcast_task_error
from sqlalchemy.orm import Session
import json
import os

app = FastAPI(title="漫剧自动化工作台 API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/output", StaticFiles(directory="output"), name="output")

init_db()

writer_agent = WriterAgent()
director_agent = DirectorAgent()

@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await ws_manager.connect(project_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(project_id, websocket)

@app.post("/projects")
def create_project(title: str = Form(...), description: Optional[str] = Form(None), db: Session = Depends(get_db)):
    project_id = str(uuid4())
    
    db_project = DBProject(
        id=project_id,
        title=title,
        description=description
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return {"id": db_project.id, "title": db_project.title, "description": db_project.description, "created_at": db_project.created_at}

@app.get("/projects/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project

@app.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    return db.query(DBProject).all()

@app.post("/projects/{project_id}/script")
def generate_script(project_id: str, request: ScriptRequest, db: Session = Depends(get_db)):
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    try:
        script_response = writer_agent.process_script(request.raw_text)
        return script_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/{project_id}/storyboard")
def generate_storyboard(project_id: str, script: ScriptResponse, db: Session = Depends(get_db)):
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    try:
        storyboard = director_agent.generate_storyboard(script)
        
        db.query(Shot).filter(Shot.project_id == project_id).delete()
        
        for shot in storyboard.shots:
            db_shot = Shot(
                id=str(uuid4()),
                project_id=project_id,
                shot_id=shot.shot_id,
                scene_type=shot.scene_type,
                duration=shot.duration,
                camera_movement=shot.camera_movement,
                visual_description=shot.visual_description,
                character_emotion=shot.character_emotion,
                dialogue=shot.dialogue,
                narration=shot.narration,
                image_url=shot.image_url
            )
            db.add(db_shot)
        
        db.commit()
        return storyboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/storyboard")
def get_storyboard(project_id: str, db: Session = Depends(get_db)):
    shots = db.query(Shot).filter(Shot.project_id == project_id).order_by(Shot.shot_id).all()
    if not shots:
        raise HTTPException(status_code=404, detail="分镜不存在")
    return {"shots": shots}

@app.put("/projects/{project_id}/storyboard/{shot_id}")
def update_shot(project_id: str, shot_id: int, request: ShotUpdateRequest, db: Session = Depends(get_db)):
    shot = db.query(Shot).filter(Shot.project_id == project_id, Shot.shot_id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="镜头不存在")
    
    if request.scene_type is not None:
        shot.scene_type = request.scene_type
    if request.duration is not None:
        shot.duration = request.duration
    if request.camera_movement is not None:
        shot.camera_movement = request.camera_movement
    if request.visual_description is not None:
        shot.visual_description = request.visual_description
    if request.character_emotion is not None:
        shot.character_emotion = request.character_emotion
    if request.dialogue is not None:
        shot.dialogue = request.dialogue
    if request.narration is not None:
        shot.narration = request.narration
    
    db.commit()
    db.refresh(shot)
    
    shots = db.query(Shot).filter(Shot.project_id == project_id).order_by(Shot.shot_id).all()
    return {"shots": shots}

@app.post("/projects/{project_id}/characters")
def add_characters(project_id: str, characters: List[CharacterCreate], db: Session = Depends(get_db)):
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    existing_names = {c.name for c in project.characters}
    new_characters = []
    
    for char_data in characters:
        if char_data.name not in existing_names:
            character = Character(
                id=str(uuid4()),
                project_id=project_id,
                name=char_data.name,
                description=char_data.description
            )
            db.add(character)
            new_characters.append(character)
    
    db.commit()
    return {"characters": [{"id": c.id, "name": c.name, "description": c.description} for c in new_characters]}

@app.get("/projects/{project_id}/characters")
def get_characters(project_id: str, db: Session = Depends(get_db)):
    characters = db.query(Character).filter(Character.project_id == project_id).all()
    result = []
    for char in characters:
        references = db.query(CharacterReference).filter(CharacterReference.character_id == char.id).all()
        result.append({
            "id": char.id,
            "name": char.name,
            "description": char.description,
            "references": [{"id": r.id, "view_type": r.view_type, "image_url": r.image_url} for r in references]
        })
    return {"characters": result}

@app.post("/projects/{project_id}/characters/{character_id}/generate")
def generate_character_references(project_id: str, character_id: str, db: Session = Depends(get_db)):
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    generate_character_task.delay(project_id, character_id)
    return {"status": "started", "message": "正在生成角色三视图"}

@app.post("/projects/{project_id}/generate-images")
def generate_images(project_id: str, db: Session = Depends(get_db)):
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    shots = db.query(Shot).filter(Shot.project_id == project_id).all()
    if not shots:
        raise HTTPException(status_code=404, detail="没有分镜数据")
    
    shots_data = [{"shot_id": s.shot_id, "visual_description": s.visual_description} for s in shots]
    generate_images_task.delay(project_id, shots_data)
    return {"status": "started", "message": "正在批量生图"}

@app.post("/projects/{project_id}/storyboard/{shot_id}/regenerate")
def regenerate_shot(project_id: str, shot_id: int, db: Session = Depends(get_db)):
    shot = db.query(Shot).filter(Shot.project_id == project_id, Shot.shot_id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="镜头不存在")
    
    regenerate_shot_task.delay(project_id, shot_id)
    return {"status": "started", "message": "正在重绘该镜头"}

@app.post("/projects/{project_id}/generate-voice")
def generate_voice(project_id: str, script: ScriptResponse, db: Session = Depends(get_db)):
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    script_data = {
        "dialogues": [{"speaker": d.speaker, "text": d.text} for d in script.dialogues],
        "narrations": [{"text": n.text} for n in script.narrations]
    }
    generate_voice_task.delay(project_id, script_data)
    return {"status": "started", "message": "正在生成配音"}

@app.get("/projects/{project_id}/tasks")
def get_tasks(project_id: str, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.project_id == project_id).order_by(Task.created_at.desc()).all()
    return {"tasks": [{"id": t.id, "task_type": t.task_type.value, "status": t.status.value, "progress": t.progress, "message": t.message, "result": t.result} for t in tasks]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
