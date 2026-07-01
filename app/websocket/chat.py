from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import ChatMessage, Booking
from typing import Dict, List
import json

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# ─── Connection Manager ───────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        # booking_id -> list of WebSocket connections
        self.active: Dict[int, List[WebSocket]] = {}

    async def connect(self, booking_id: int, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(booking_id, []).append(ws)

    def disconnect(self, booking_id: int, ws: WebSocket):
        if booking_id in self.active:
            self.active[booking_id].remove(ws)

    async def broadcast(self, booking_id: int, message: dict):
        for ws in self.active.get(booking_id, []):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                pass


manager = ConnectionManager()


# ─── WebSocket Endpoint ───────────────────────────────────────────────────────

router = APIRouter()

@router.websocket("/ws/{booking_id}/{sender_type}/{sender_id}")
async def websocket_chat(
    booking_id: int,
    sender_type: str,
    sender_id: int,
    websocket: WebSocket,
    db: Session = Depends(get_db),
):
    # Validate booking exists
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        await websocket.close(code=4004)
        return

    await manager.connect(booking_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            msg_type = data.get("type", "text")
            content  = data.get("content", "")

            # Save to DB
            msg = ChatMessage(
                booking_id=booking_id,
                sender_type=sender_type,
                sender_id=sender_id,
                message_type=msg_type,
                content=content,
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)

            # Broadcast to all in this booking room
            await manager.broadcast(booking_id, {
                "id": msg.id,
                "sender_type": sender_type,
                "sender_id": sender_id,
                "message_type": msg_type,
                "content": content,
                "sent_at": msg.sent_at.isoformat(),
            })

    except WebSocketDisconnect:
        manager.disconnect(booking_id, websocket)


# ─── REST: Load previous messages ─────────────────────────────────────────────

@router.get("/{booking_id}/messages")
def get_messages(booking_id: int, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(
        ChatMessage.booking_id == booking_id
    ).order_by(ChatMessage.sent_at.asc()).all()

    return [
        {
            "id": m.id,
            "sender_type": m.sender_type,
            "sender_id": m.sender_id,
            "message_type": m.message_type,
            "content": m.content,
            "is_read": m.is_read,
            "sent_at": m.sent_at.isoformat(),
        }
        for m in messages
    ]
