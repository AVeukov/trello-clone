from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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