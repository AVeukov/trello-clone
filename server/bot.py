from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
from models import SessionLocal, UserSubscription
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    logger.info(f"Получена команда /start от пользователя {update.effective_user.id}")
    await update.message.reply_text(
        "Привет! Я бот для уведомлений о задачах в вашем Trello-подобном приложении.\n\n"
        "Чтобы начать получать уведомления, пожалуйста, введите ваш GitHub логин:"
    )

async def handle_github_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода GitHub логина"""
    github_username = update.message.text.strip()
    logger.info(f"Получен GitHub логин: {github_username} от пользователя {update.effective_user.id}")
    
    # Сохранение подписки в базу данных
    db = SessionLocal()
    try:
        # Проверяем, не подписан ли уже пользователь
        existing = db.query(UserSubscription).filter(
            UserSubscription.github_username == github_username
        ).first()
        
        if existing:
            logger.info(f"Пользователь {github_username} уже подписан")
            await update.message.reply_text(
                f"Пользователь {github_username} уже подписан на уведомления."
            )
            return

        subscription = UserSubscription(
            github_username=github_username,
            telegram_chat_id=str(update.effective_chat.id)
        )
        db.add(subscription)
        db.commit()
        logger.info(f"Успешно добавлена подписка для {github_username}")
        await update.message.reply_text(
            f"Отлично! Вы успешно подписались на уведомления.\n"
            f"Ваш GitHub аккаунт: {github_username}\n\n"
            "Теперь вы будете получать уведомления за день до дедлайна задачи."
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении подписки: {str(e)}")
        db.rollback()
        await update.message.reply_text("Произошла ошибка при сохранении подписки.")
    finally:
        db.close()

async def send_telegram_notification(message: str):
    """Отправка уведомления в Telegram"""
    try:
        bot = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
        db = SessionLocal()
        subscriptions = db.query(UserSubscription).all()
        
        for subscription in subscriptions:
            await bot.bot.send_message(
                chat_id=subscription.telegram_chat_id,
                text=message
            )
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {str(e)}")
        return False
    finally:
        db.close()

def main():
    """Запуск бота"""
    logger.info("Запуск бота...")
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_github_username))
    
    # Запуск бота
    logger.info("Бот запущен и готов к работе")
    application.run_polling()

if __name__ == "__main__":
    main() 