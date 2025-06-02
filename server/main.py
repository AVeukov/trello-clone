from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import telegram
import asyncio
from typing import Optional
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from users import register_user, verify_user, generate_token, verify_token

# Загрузка переменных окружения
load_dotenv()

# Инициализация FastAPI
app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка кодировки для JSON
class CustomJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            indent=2
        ).encode("utf-8")

# Настройка базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./notifications.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модель базы данных
class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    github_username = Column(String, unique=True, index=True)
    telegram_chat_id = Column(String, unique=True, index=True)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Pydantic модели
class SubscriptionCreate(BaseModel):
    github_username: str
    telegram_chat_id: str

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Инициализация бота
bot = telegram.Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

# Глобальная переменная для хранения данных досок
boards_data = {}

@app.post("/subscribe")
async def subscribe(subscription: SubscriptionCreate, db: Session = Depends(get_db)):
    # Проверка существующей подписки
    existing = db.query(UserSubscription).filter(
        UserSubscription.github_username == subscription.github_username
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already subscribed")
    
    # Создание новой подписки
    db_subscription = UserSubscription(
        github_username=subscription.github_username,
        telegram_chat_id=subscription.telegram_chat_id
    )
    db.add(db_subscription)
    db.commit()
    
    return {"message": "Successfully subscribed"}

@app.post("/send-notification")
async def send_notification(github_username: str, task_name: str, deadline: str):
    db = SessionLocal()
    try:
        # Получение chat_id пользователя
        subscription = db.query(UserSubscription).filter(
            UserSubscription.github_username == github_username
        ).first()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Отправка уведомления
        message = f"⚠️ Напоминание о задаче!\n\nЗадача: {task_name}\nСрок: {deadline}"
        await bot.send_message(chat_id=subscription.telegram_chat_id, text=message)
        
        return {"message": "Notification sent"}
    finally:
        db.close()

# Функция для проверки и отправки уведомлений
async def check_and_send_notifications():
    while True:
        db = SessionLocal()
        try:
            # Получаем все подписки
            subscriptions = db.query(UserSubscription).all()
            
            # Получаем все задачи из localStorage
            boards_data = {}  # Здесь нужно будет добавить доступ к данным досок
            
            for subscription in subscriptions:
                # Проверяем задачи для каждого пользователя
                for board in boards_data.values():
                    for column in board.get('columns', []):
                        for card in column.get('cards', []):
                            if not card.get('date'):
                                continue
                                
                            deadline = datetime.strptime(card['date'], '%Y-%m-%d')
                            tomorrow = datetime.now() + timedelta(days=1)
                            
                            # Если дедлайн завтра, отправляем уведомление
                            if deadline.date() == tomorrow.date():
                                try:
                                    message = (
                                        f"⚠️ Напоминание о задаче!\n\n"
                                        f"Задача: {card['text']}\n"
                                        f"Колонка: {column['title']}\n"
                                        f"Срок: {card['date']} {card.get('time', '09:00')}\n"
                                    )
                                    if card.get('description'):
                                        message += f"\nОписание: {card['description']}"
                                        
                                    await bot.send_message(
                                        chat_id=subscription.telegram_chat_id,
                                        text=message
                                    )
                                except Exception as e:
                                    print(f"Ошибка отправки уведомления: {e}")
                                    
        except Exception as e:
            print(f"Ошибка проверки уведомлений: {e}")
        finally:
            db.close()
            
        # Проверяем каждый час
        await asyncio.sleep(3600)

@app.post("/sync-boards")
async def sync_boards(boards: dict):
    global boards_data
    boards_data = boards
    return CustomJSONResponse(content={"message": "Boards synchronized successfully"})

@app.get("/get-boards")
async def get_boards():
    return CustomJSONResponse(content=boards_data)

# Добавляем периодическую синхронизацию
async def periodic_sync():
    while True:
        try:
            # Здесь можно добавить дополнительную логику синхронизации
            # например, сохранение в базу данных или другие операции
            await asyncio.sleep(300)  # Синхронизация каждые 5 минут
        except Exception as e:
            print(f"Ошибка при периодической синхронизации: {e}")
            await asyncio.sleep(60)  # При ошибке ждем минуту

# Запускаем периодическую синхронизацию при старте сервера
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_and_send_notifications())
    asyncio.create_task(periodic_sync())

@app.post("/test-notification")
async def test_notification():
    try:
        # Получаем все подписки
        db = SessionLocal()
        subscriptions = db.query(UserSubscription).all()
        
        # Отправляем тестовое уведомление каждому подписчику
        for sub in subscriptions:
            await bot.send_message(
                chat_id=sub.telegram_chat_id,
                text="🔔 Тестовое уведомление!\n\nЭто тестовое сообщение для проверки работы системы уведомлений."
            )
        
        return {"status": "success", "message": "Тестовые уведомления отправлены"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password:
        return jsonify({'error': 'Необходимо указать имя пользователя и пароль'}), 400
    
    if register_user(username, password, email):
        token = generate_token(username)
        return jsonify({'token': token, 'username': username}), 200
    else:
        return jsonify({'error': 'Пользователь с таким именем уже существует'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Необходимо указать имя пользователя и пароль'}), 400
    
    if verify_user(username, password):
        token = generate_token(username)
        return jsonify({'token': token, 'username': username}), 200
    else:
        return jsonify({'error': 'Неверное имя пользователя или пароль'}), 401

@app.route('/verify-token', methods=['POST'])
def verify_token_route():
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'error': 'Токен не предоставлен'}), 400
    
    username = verify_token(token)
    if username:
        return jsonify({'username': username}), 200
    else:
        return jsonify({'error': 'Недействительный токен'}), 401

# Модифицируем существующие эндпоинты для работы с пользователями
@app.route('/sync-boards', methods=['POST'])
def sync_boards():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    username = verify_token(token)
    if not username:
        return jsonify({'error': 'Недействительный токен'}), 401
    
    data = request.get_json()
    filename = f'data/boards_{username}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return jsonify({'status': 'success'})

@app.route('/get-boards', methods=['GET'])
def get_boards():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    username = verify_token(token)
    if not username:
        return jsonify({'error': 'Недействительный токен'}), 401
    
    filename = f'data/boards_{username}.json'
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify({}) 