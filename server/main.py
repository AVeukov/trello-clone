from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
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

# Запуск проверки уведомлений при старте сервера
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_and_send_notifications())

@app.post("/sync-boards")
async def sync_boards(boards: dict):
    global boards_data
    boards_data = boards
    return {"message": "Boards synchronized successfully"} 