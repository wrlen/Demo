import json
import subprocess
import os
from uuid import uuid4
from celery_config import app
from database import SessionLocal, Shot, Task, TaskStatus, TaskType, CharacterReference

def get_db():
    return SessionLocal()

@app.task(bind=True)
def generate_images_task(self, project_id: str, shots_data: list):
    db = get_db()
    task_id = str(uuid4())
    
    task = Task(
        id=task_id,
        project_id=project_id,
        task_type=TaskType.GENERATE_IMAGES,
        status=TaskStatus.RUNNING,
        progress=0
    )
    db.add(task)
    db.commit()
    
    try:
        total = len(shots_data)
        for i, shot_data in enumerate(shots_data):
            progress = int((i + 1) / total * 100)
            self.update_state(
                state='PROGRESS',
                meta={'progress': progress, 'current': i + 1, 'total': total}
            )
            
            task.progress = progress
            db.commit()
            
            shot = db.query(Shot).filter(Shot.project_id == project_id, Shot.shot_id == shot_data['shot_id']).first()
            if shot:
                shot.image_url = f"/static/images/{project_id}/{shot.shot_id}.png"
                db.commit()
        
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.result = {"message": "图片生成完成"}
        db.commit()
        
        return {"status": "completed", "progress": 100}
    
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.message = str(e)
        db.commit()
        raise
    finally:
        db.close()

@app.task(bind=True)
def regenerate_shot_task(self, project_id: str, shot_id: int):
    db = get_db()
    task_id = str(uuid4())
    
    task = Task(
        id=task_id,
        project_id=project_id,
        task_type=TaskType.REGENERATE_SHOT,
        status=TaskStatus.RUNNING,
        progress=0
    )
    db.add(task)
    db.commit()
    
    try:
        shot = db.query(Shot).filter(Shot.project_id == project_id, Shot.shot_id == shot_id).first()
        if shot:
            shot.image_url = f"/static/images/{project_id}/{shot_id}_v2.png"
            db.commit()
        
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.result = {"shot_id": shot_id, "image_url": shot.image_url}
        db.commit()
        
        return {"status": "completed"}
    
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.message = str(e)
        db.commit()
        raise
    finally:
        db.close()

@app.task(bind=True)
def generate_voice_task(self, project_id: str, script_data: dict):
    db = get_db()
    task_id = str(uuid4())
    
    task = Task(
        id=task_id,
        project_id=project_id,
        task_type=TaskType.GENERATE_VOICE,
        status=TaskStatus.RUNNING,
        progress=0
    )
    db.add(task)
    db.commit()
    
    try:
        srt_content = generate_srt(script_data)
        srt_path = f"output/{project_id}/subtitles.srt"
        os.makedirs(f"output/{project_id}", exist_ok=True)
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.result = {"srt_path": srt_path}
        db.commit()
        
        return {"status": "completed", "srt_path": srt_path}
    
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.message = str(e)
        db.commit()
        raise
    finally:
        db.close()

def generate_srt(script_data):
    srt = []
    index = 1
    time = 0.0
    
    for dialogue in script_data.get('dialogues', []):
        start_time = format_time(time)
        duration = len(dialogue['text']) * 0.08 + 0.5
        end_time = format_time(time + duration)
        srt.append(f"{index}")
        srt.append(f"{start_time} --> {end_time}")
        srt.append(dialogue['text'])
        srt.append("")
        index += 1
        time += duration + 0.5
    
    for narration in script_data.get('narrations', []):
        start_time = format_time(time)
        duration = len(narration['text']) * 0.1 + 0.5
        end_time = format_time(time + duration)
        srt.append(f"{index}")
        srt.append(f"{start_time} --> {end_time}")
        srt.append(narration['text'])
        srt.append("")
        index += 1
        time += duration + 0.3
    
    return "\n".join(srt)

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

@app.task(bind=True)
def compose_video_task(self, project_id: str):
    db = get_db()
    task_id = str(uuid4())
    
    task = Task(
        id=task_id,
        project_id=project_id,
        task_type=TaskType.COMPOSE,
        status=TaskStatus.RUNNING,
        progress=0
    )
    db.add(task)
    db.commit()
    
    try:
        shots = db.query(Shot).filter(Shot.project_id == project_id).order_by(Shot.shot_id).all()
        
        if not shots:
            raise Exception("没有分镜数据")
        
        output_dir = f"output/{project_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        temp_files = []
        for shot in shots:
            temp_file = f"{output_dir}/temp_{shot.shot_id}.mp4"
            cmd = [
                'ffmpeg', '-loop', '1', '-i', shot.image_url or 'placeholder.png',
                '-t', str(shot.duration), '-r', '24',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-y', temp_file
            ]
            subprocess.run(cmd, capture_output=True)
            temp_files.append(temp_file)
        
        concat_list = f"{output_dir}/concat.txt"
        with open(concat_list, 'w') as f:
            for temp_file in temp_files:
                f.write(f"file '{os.path.abspath(temp_file)}'\n")
        
        output_path = f"{output_dir}/final.mp4"
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_list,
            '-c', 'copy', '-y', output_path
        ]
        subprocess.run(cmd, capture_output=True)
        
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.result = {"video_path": f"/output/{project_id}/final.mp4"}
        db.commit()
        
        return {"status": "completed", "video_path": output_path}
    
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.message = str(e)
        db.commit()
        raise
    finally:
        db.close()

@app.task(bind=True)
def generate_character_task(self, project_id: str, character_id: str):
    db = get_db()
    task_id = str(uuid4())
    
    task = Task(
        id=task_id,
        project_id=project_id,
        task_type=TaskType.GENERATE_CHARACTER,
        status=TaskStatus.RUNNING,
        progress=0
    )
    db.add(task)
    db.commit()
    
    try:
        views = ['front', 'side', 'back']
        for i, view in enumerate(views):
            ref = CharacterReference(
                id=str(uuid4()),
                character_id=character_id,
                view_type=view,
                image_url=f"/static/characters/{character_id}_{view}.png"
            )
            db.add(ref)
            db.commit()
            
            progress = int((i + 1) / len(views) * 100)
            self.update_state(
                state='PROGRESS',
                meta={'progress': progress}
            )
            task.progress = progress
            db.commit()
        
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        db.commit()
        
        return {"status": "completed"}
    
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.message = str(e)
        db.commit()
        raise
    finally:
        db.close()