import logging
import sqlite3
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from dotenv import load_dotenv
from pathlib import Path
import csv


# Файл базы данных
DATABASE = 'teamy_bot.db'

load_dotenv(dotenv_path=Path('.') / 'config.env')

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_FIL_UID = int(os.getenv("ADMIN_FIL_UID"))
SECRET_CODE = os.getenv("SECRET_CODE")         # Код для получения статистики
CLEAR_DB_CODE = os.getenv("CLEAR_DB_CODE")       # Код для очистки базы данных


def init_db():
    """Инициализирует базу данных (создает таблицу, если не существует)."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            start_count INTEGER DEFAULT 0,
            analyze_team_count INTEGER DEFAULT 0,
            analyze_team_roles_count INTEGER DEFAULT 0,
            analyze_for_all_count INTEGER DEFAULT 0,
            analyze_for_me_count INTEGER DEFAULT 0,
            summarize_full_count INTEGER DEFAULT 0,
            summarize_min_count INTEGER DEFAULT 0,
            tz_count INTEGER DEFAULT 0,
            premium_count INTEGER DEFAULT 0,
            agree_count INTEGER DEFAULT 0,
            settings_count INTEGER DEFAULT 0,
            ai_count INTEGER DEFAULT 0
            )
        ''')
    conn.commit()
    conn.close()


def fetch_user_data(export=False):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Выбираем все данные из таблицы users
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    conn.close()
    if export:
        with open('users_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'user_id', 'start_count', 'analyze_team_count', 'analyze_team_roles_count',
                'analyze_for_all_count', 'analyze_for_me_count', 'summarize_full_count',
                'summarize_min_count', 'tz_count', 'premium_count', 'agree_count',
                'settings_count', 'ai_count'
            ])
            writer.writerows(rows)
    return rows


def log_command(user_id: int, command: str):
    """Логирует вызов команды для пользователя в базу данных."""
    # Словарь сопоставления команды с названием столбца
    command_to_column = {
        '/start': 'start_count',
        '/analyze_team': 'analyze_team_count',
        '/analyze_team_roles': 'analyze_team_roles_count',
        '/analyze_for_all': 'analyze_for_all_count',
        '/analyze_for_me': 'analyze_for_me_count',
        '/summarize_full': 'summarize_full_count',
        '/summarize_min': 'summarize_min_count',
        '/tz': 'tz_count',
        '/premium': 'premium_count',
        '/agree': 'agree_count',
        '/settings': 'settings_count',
        '/ai': 'ai_count'
    }
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Если пользователь отсутствует, добавляем его
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if c.fetchone() is None:
        c.execute('''
            INSERT INTO users (
                user_id, start_count, analyze_team_count, analyze_team_roles_count, analyze_for_all_count,
                analyze_for_me_count, summarize_full_count, summarize_min_count, tz_count,
                premium_count, agree_count, settings_count, ai_count
            )
            VALUES (?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        ''', (user_id,))
    # Обновляем счетчик для соответствующей команды
    if command in command_to_column:
        column = command_to_column[command]
        c.execute(f"UPDATE users SET {column} = {column} + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def start_command(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    chat_type = update.effective_chat.type
    if chat_type == 'private':
        text = (
            "👋 Привет! Я - бот Teamy - создан для повышения эффективности командной работы:\n\n"
            "/analyze_team - оценить общий уровень командной работы\n" 
            "/analyze_team_roles - узнать роль каждого участника\n" 
            "/analyze_for_all  -  Оценить навыки командной работы каждого участника\n" 
            "/analyze_for_me - Оценить ваши личные навыки командной работы\n"
            "/summarize_full - Получить выжимку переписки с акцентом на детали и ваши задачи\n"
            "/summarize_min - Получить сжатый обзор последних сообщений чата\n"
            "/tz - Составить структурированное техническое задания (ТЗ)\n"
            "Саммари ГС - Получить выжимку из длинного голосового сообщения\n\n"
            "Добавь меня в чат вашей команды и получи БЕСПЛАТНО "
            "Подписку на 7 дней и 9 запросов для каждого участника чата!"
        )
        update.message.reply_text(text)
    else:
        # Если команда /start вызвана в чате (группе)
        text = (
            "👋 Привет! Я - бот Teamy - создан для повышения эффективности командной работы:\n\n"
            "/analyze_team - оценить общий уровень командной работы\n" 
            "/analyze_team_roles - узнать роль каждого участника\n" 
            "/analyze_for_all  -  Оценить навыки командной работы каждого участника\n" 
            "/analyze_for_me - Оценить ваши личные навыки командной работы\n"
            "/summarize_full - Получить выжимку переписки с акцентом на детали и ваши задачи\n"
            "/summarize_min - Получить сжатый обзор последних сообщений чата\n"
            "/tz - Составить структурированное техническое задания (ТЗ)\n"
            "Саммари ГС - Получить выжимку из длинного голосового сообщения\n\n"
            "Добавь меня в чат вашей команды и получи БЕСПЛАТНО "
            "Подписку на 7 дней и 9 запросов для каждого участника чата!"
        )
        update.message.reply_text(text)
    # Логирование вызова команды
    log_command(user.id, '/start')


def fallback_command(update: Update, context: CallbackContext) -> None:
    """Обработчик для остальных команд, не реализованных на данный момент."""
    text = (
        "Благодарим за интерес к боту Teamy! Предлагаем подписаться на наш Телеграм канал (@V_komade) и быть в курсе "
        "всех новостей. Полный релиз бота запланирован на начало мая 2025 года."
    )
    update.message.reply_text(text)
    # Определяем команду из текста сообщения
    command = update.message.text.split()[0]
    log_command(update.effective_user.id, command)


def new_chat_members(update: Update, context: CallbackContext) -> None:
    """Обработчик для события добавления бота в группу."""
    for new_member in update.message.new_chat_members:
        if new_member.id == context.bot.id:
            text = (
                "👋 Привет! Я - бот Teamy - создан для повышения эффективности командной работы:\n\n"
                "/analyze_team - оценить общий уровень командной работы\n" 
                "/analyze_team_roles - узнать роль каждого участника\n" 
                "/analyze_for_all  -  Оценить навыки командной работы каждого участника\n" 
                "/analyze_for_me - Оценить ваши личные навыки командной работы\n"
                "/summarize_full - Получить выжимку переписки с акцентом на детали и ваши задачи\n"
                "/summarize_min - Получить сжатый обзор последних сообщений чата\n"
                "/tz - Составить структурированное техническое задания (ТЗ)\n"
                "Саммари ГС - Получить выжимку из длинного голосового сообщения\n\n"
                "Добавь меня в чат вашей команды и получи БЕСПЛАТНО "
                "Подписку на 7 дней и 9 запросов для каждого участника чата!"
            )
            update.message.reply_text(text)
            break


def admin_secret_handler(update: Update, context: CallbackContext) -> None:
    """
    Секретный обработчик для администратора.
    Если в личном чате получено текстовое сообщение, равное кодовому слову,
    и user_id отправителя соответствует ADMIN_USER_ID, то бот выполняет функцию
    по извлечению статистики (например, экспортирует данные из базы в CSV).
    """
    if update.effective_chat.type != 'private':
        return

    text = update.message.text.strip()
    if text == SECRET_CODE:
        if update.effective_user.id == ADMIN_FIL_UID:
            # Получаем данные из базы и экспортируем их в CSV
            fetch_user_data(export=True)
            try:
                with open('users_data.csv', 'rb') as csvfile:
                    update.message.reply_document(document=csvfile, filename='users_data.csv')
            except Exception as e:
                update.message.reply_text(f"Ошибка при отправке файла: {e}")
        else:
            update.message.reply_text("Access denied: Вы не авторизованы для выполнения этой команды.")
    elif text == CLEAR_DB_CODE:
        if update.effective_user.id == ADMIN_FIL_UID:
            try:
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users")
                conn.commit()
                conn.close()
                update.message.reply_text("База данных успешно очищена.")
            except Exception as e:
                update.message.reply_text(f"Ошибка при очистке базы данных: {e}")
        else:
            update.message.reply_text("Access denied: Вы не авторизованы для выполнения этой команды.")


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )
    init_db()

    if not TELEGRAM_BOT_TOKEN:
        print("Ошибка: переменная окружения TELEGRAM_BOT_TOKEN не установлена.")
        return

    updater = Updater(
        TELEGRAM_BOT_TOKEN,
        request_kwargs={'read_timeout': 20, 'connect_timeout': 20}
    )
    dispatcher = updater.dispatcher

    # Регистрируем обработчик для /start
    dispatcher.add_handler(CommandHandler("start", start_command))

    # Регистрируем обработчики для остальных команд
    commands = [
        "analyze_team", "analyze_team_roles", "analyze_for_all", "analyze_for_me",
        "summarize_full", "summarize_min", "tz", "premium", "agree", "settings", "ai"
    ]
    for cmd in commands:
        dispatcher.add_handler(CommandHandler(cmd, fallback_command))
    # Обработчик события добавления бота в группу
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_chat_members))
    # Регистрируем секретный обработчик для текстовых сообщений в личных чатах
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.chat_type.private, admin_secret_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
