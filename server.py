import os
import uuid
import random
import sqlite3
import base64
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Ione Messenger API")

# --- Database Setup ---
DB_PATH = "ione.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT,
            password TEXT NOT NULL,
            avatar_url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            content TEXT,
            msg_type TEXT, -- 'text', 'image', 'voice'
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Models ---
class UserRegister(BaseModel):
    username: str
    password: str
    display_name: str = None

class UserLogin(BaseModel):
    username: str
    password: str

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()

# --- API Endpoints ---

@app.post("/register")
async def register(user: UserRegister):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Generate 8-digit unique ID
    while True:
        user_id = random.randint(10000000, 99999999)
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            break
            
    display_name = user.display_name or user.username
    cursor.execute(
        "INSERT INTO users (id, username, display_name, password) VALUES (?, ?, ?, ?)",
        (user_id, user.username, display_name, user.password)
    )
    conn.commit()
    conn.close()
    return {"id": user_id, "username": user.username, "display_name": display_name}

@app.post("/login")
async def login(user: UserLogin):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, display_name FROM users WHERE username = ? AND password = ?",
        (user.username, user.password)
    )
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {"id": result[0], "username": result[1], "display_name": result[2]}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# --- WebSocket Endpoint ---
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # data format: {"content": "...", "type": "text/image/voice"}
            
            # Save to DB
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (sender_id, content, msg_type) VALUES (?, ?, ?)",
                (user_id, data.get("content"), data.get("type", "text"))
            )
            conn.commit()
            
            # Fetch user info for display
            cursor.execute("SELECT display_name FROM users WHERE id = ?", (user_id,))
            user_info = cursor.fetchone()
            conn.close()
            
            broadcast_msg = {
                "sender_id": user_id,
                "sender_name": user_info[0] if user_info else "Unknown",
                "content": data.get("content"),
                "type": data.get("type", "text")
            }
            await manager.broadcast(broadcast_msg)
    except WebSocketDisconnect:
        manager.disconnect(user_id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
