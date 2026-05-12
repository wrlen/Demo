from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

SQLALCHEMY_DATABASE_URL = "sqlite:///./demo.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(str, enum.Enum):
    GENERATE_IMAGES = "generate_images"
    REGENERATE_SHOT = "regenerate_shot"
    GENERATE_VOICE = "generate_voice"
    COMPOSE = "compose"
    GENERATE_CHARACTER = "generate_character"

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    shots = relationship("Shot", back_populates="project")
    characters = relationship("Character", back_populates="project")
    tasks = relationship("Task", back_populates="project")

class Shot(Base):
    __tablename__ = "shots"
    
    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id"))
    shot_id = Column(Integer)
    scene_type = Column(String)
    duration = Column(Float)
    camera_movement = Column(String)
    visual_description = Column(Text)
    character_emotion = Column(String)
    dialogue = Column(Text)
    narration = Column(Text)
    image_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="shots")

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id"))
    name = Column(String, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="characters")
    references = relationship("CharacterReference", back_populates="character")

class CharacterReference(Base):
    __tablename__ = "character_references"
    
    id = Column(String, primary_key=True, index=True)
    character_id = Column(String, ForeignKey("characters.id"))
    view_type = Column(Enum("front", "side", "back", name="view_types"))
    image_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    character = relationship("Character", back_populates="references")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id"))
    task_type = Column(Enum(TaskType))
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Integer, default=0)
    message = Column(Text)
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="tasks")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)