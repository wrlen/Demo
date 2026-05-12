from typing import Dict, List
from fastapi import WebSocket
import json
import asyncio

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)

    def disconnect(self, project_id: str, websocket: WebSocket):
        if project_id in self.active_connections:
            if websocket in self.active_connections[project_id]:
                self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    async def send_progress(self, project_id: str, progress_data: dict):
        if project_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_json(progress_data)
                except Exception:
                    dead_connections.append(connection)

            for dead in dead_connections:
                self.disconnect(project_id, dead)

    async def broadcast_to_project(self, project_id: str, message: dict):
        await self.send_progress(project_id, message)

ws_manager = WebSocketManager()

async def broadcast_progress(project_id: str, progress: int, task_type: str, message: str = "", current: int = 0, total: int = 0):
    await ws_manager.send_progress(project_id, {
        "type": "progress",
        "task_type": task_type,
        "progress": progress,
        "message": message,
        "current": current,
        "total": total
    })

async def broadcast_task_complete(project_id: str, task_type: str, result: dict):
    await ws_manager.send_progress(project_id, {
        "type": "task_complete",
        "task_type": task_type,
        "result": result
    })

async def broadcast_task_error(project_id: str, task_type: str, error: str):
    await ws_manager.send_progress(project_id, {
        "type": "task_error",
        "task_type": task_type,
        "error": error
    })