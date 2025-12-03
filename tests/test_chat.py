import asyncio
import websockets
import json
import requests


LOGIN_URL = "http://localhost:8000/api/v1/login"
WS_URL = "ws://localhost:8000/api/v1/ws/chat"


USER_CREDENTIALS = {
    "email": "karacuna396@gmail.com",
    "password": "123456789"
}

def get_access_token():
    try:
        response = requests.post(LOGIN_URL, json=USER_CREDENTIALS)
        response.raise_for_status()
        token = response.json().get("access_token")
        print(f"✅ Токен получен: {token}")
        return token
    except Exception as e:
        print(f"❌ Ошибка получения токена: {e}")
        if 'response' in locals():
            print(f"Ответ сервера: {response.text}")
        return None


async def test_websocket():
    token = get_access_token()
    if not token:
        print("❌ Тест прерван: токен не получен.")
        return

    uri = f"{WS_URL}?token={token}"
    print(f"🔗 Подключение к WebSocket: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Подключение установлено")

            response = await websocket.recv()
            print(f"📥 Получено подтверждение: {response}")

            test_message_1 = {"message": "Hello, WebSocket!"}
            await websocket.send(json.dumps(test_message_1))
            print(f"📤 Отправлено: {test_message_1}")

            response = await websocket.recv()
            print(f"📥 Получено: {response}")

            test_message_2 = {"message": "How are you?"}
            await websocket.send(json.dumps(test_message_2))
            print(f"📤 Отправлено: {test_message_2}")

            response = await websocket.recv()
            print(f"📥 Получено: {response}")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Соединение закрыто: {e.code} - {e.reason}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
