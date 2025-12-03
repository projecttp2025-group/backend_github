import logging
import traceback
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import User, Account
from app.services.chat_manager import chat_manager

router = APIRouter()
logger = logging.getLogger("app.chat")

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008, reason="Token required")
        return

    db = None
    try:
        db = next(get_db())  # забрать следующий объект из функции-генератора get_db()

        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_alg],
                options={"require": ["exp", "iat"]},
            )
        except jwt.ExpiredSignatureError:
            await websocket.close(code=1008, reason="Token has expired")
            return
        except jwt.InvalidTokenError as e:
            await websocket.close(code=1008, reason=f"Invalid token: {str(e)}")
            return
        
        if payload.get("type") != "access":
            await websocket.close(code=1008, reason="Token type is not access")
            return

        email = payload["sub"]
        user_data = db.query(User).join(Account, Account.user_id == User.id).filter(User.email == email).first()

        if not user_data:
            await websocket.close(code=1008, reason="User not found")
            return
        
        user_id = user_data.id
        is_admin = user_data.is_admin
        logger.info(f"User {user_id} connected as {'admin' if is_admin else 'user'}")

        await chat_manager.connect(websocket=websocket, user_id=user_id, is_admin=is_admin)

        await websocket.send_json({
            "status": "connected", 
            "user_id": user_id, 
            "is_admin": is_admin,
            "message": f"User {user_id} connected as {'admin' if is_admin else 'user'}"
        })

        while True:
            try:
                data = await websocket.receive_json()
                message = data.get("message")
                
                if not message:
                    await websocket.send_json({"error": "Missing message field"})
                    continue
                
                if is_admin:
                    target_user_id = data.get("to_user")
                    if target_user_id:
                        await chat_manager.send_to_user(target_user_id, message)
                        await websocket.send_json({
                            "status": "message_sent", 
                            "to_user": target_user_id,
                            "message": message
                        })
                    else:
                        await websocket.send_json({"error": "Missing to_user field for admin"})
                else:
                    await chat_manager.send_to_admin(user_id, message)
                    await websocket.send_json({
                        "status": "message_sent_to_admin",
                        "message": message
                    })
            except WebSocketDisconnect:
                logger.info(f"User {user_id} disconnected")
                chat_manager.disconnect(user_id, is_admin)
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.debug(traceback.format_exc())
                break


    except Exception as e:
        logger.error(f"Critical WebSocket Error: {e}")
        logger.debug(traceback.format_exc())
        if 'user_id' in locals() and 'is_admin' in locals():
            chat_manager.disconnect(user_id, is_admin)
    finally:
        if db:
            db.close()

    
@router.post("/chat")
def chat(request: dict, db: Session = Depends(get_db)):
    """
    Пример HTTP endpoint для тестирования чата.
    """
    logger.info("HTTP /chat endpoint called")
    return {"message": "Chat endpoint is working"}