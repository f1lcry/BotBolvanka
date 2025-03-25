import logging
import sqlite3
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from dotenv import load_dotenv
from pathlib import Path


# Файл базы данных
DATABASE = 'teamy_bot.db'


def init_db():
    """Инициализирует базу данных (создает таблицу, если не существует)."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            start_count INTEGER DEFAULT 0,
            analyze_count INTEGER DEFAULT 0,
            analyze_for_me_count INTEGER DEFAULT 0,
            summarize_count INTEGER DEFAULT 0,
            tz_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()


def log_command(user_id: int, command: str):
    """Логирует вызов команды для пользователя в базу данных."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Если пользователь отсутствует, добавляем его
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if c.fetchone() is None:
        c.execute('''
            INSERT INTO users (user_id, start_count, analyze_count, analyze_for_me_count, summarize_count, tz_count)
            VALUES (?, 0, 0, 0, 0, 0)
        ''', (user_id,))
    # Обновляем счетчик для соответствующей команды
    if command == '/start':
        c.execute("UPDATE users SET start_count = start_count + 1 WHERE user_id = ?", (user_id,))
    elif command == '/analyze':
        c.execute("UPDATE users SET analyze_count = analyze_count + 1 WHERE user_id = ?", (user_id,))
    elif command == '/analyze_for_me':
        c.execute("UPDATE users SET analyze_for_me_count = analyze_for_me_count + 1 WHERE user_id = ?", (user_id,))
    elif command == '/summarize':
        c.execute("UPDATE users SET summarize_count = summarize_count + 1 WHERE user_id = ?", (user_id,))
    elif command in ['/тз', '/tz']:
        c.execute("UPDATE users SET tz_count = tz_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def start_command(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    chat_type = update.effective_chat.type
    if chat_type == 'private':
        text = (
            "Привет!\n\n"
            "Меня зовут “Teamy”. Я создан для повышения эффективности командной работы! 🔥\n\n"
            "Что я умею?\n\n"
            "/analyze - Помогу повысить эффективность всей команды, определить роли участников\n"
            "/analyze_for_me - Дам персональные рекомендации участнику команды\n"
            "/summarize - Кратко сформулирую ключевые тезисы и идеи переписки\n"
            "/tz -  Составлю структурированное техническое задания (ТЗ)\n\n"
            "Добавь меня в чат команды и получи бесплатный пробный период с доступом ко всем функциям!"
        )
        update.message.reply_text(text)
    else:
        # Если команда /start вызвана в чате (группе)
        text = (
            "👋 Привет! Это бот Teamy!\n\n"
            "🛠 Основные функции:\n"
            "/start - Запуск бота\n"
            "/premium - Купить подписку\n"
            "/agree - Пользовательское соглашение\n"
            "/settings - Настройки бота\n"
            "/analyze - Оценка эффективности работы команды с детальным анализом коммуникаций и советами по улучшению\n"
            "/summarize - Краткое саммари (выжимка) из переписки чата\n"
            "/analyze_for_me - Персональный анализ сообщений для отдельного пользователя\n"
            "/tz - Формирование структурированного технического задания (ТЗ)"
        )
        update.message.reply_text(text)
    # Логирование вызова команды
    log_command(user.id, '/start')


def fallback_command(update: Update, context: CallbackContext) -> None:
    """Обработчик для остальных команд, не реализованных на данный момент."""
    text = (
        "К сожалению, данная функция находится на доработке. Следите за обновлениями бота Teamy на нашем "
        "Телеграм канале @V_komade."
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
                "👋 Привет! Это бот Teamy!\n\n"
                "🛠 Основные функции:\n"
                "/start - Запуск бота\n"
                "/premium - Купить подписку\n"
                "/agree - Пользовательское соглашение\n"
                "/settings - Настройки бота\n"
                "/analyze - Оценка эффективности работы команды с детальным анализом коммуникаций и советами "
                "по улучшению\n"
                "/summarize - Краткое саммари (выжимка) из переписки чата\n"
                "/analyze_for_me - Персональный анализ сообщений для отдельного пользователя\n"
                "/tz - Формирование структурированного технического задания (ТЗ)"
            )
            update.message.reply_text(text)
            break


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )
    init_db()

    load_dotenv(dotenv_path=Path('.') / 'config.env')

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
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
    for cmd in ["analyze", "analyze_for_me", "summarize", "tz", "premium", "agree", "settings"]:
        dispatcher.add_handler(CommandHandler(cmd, fallback_command))
    # Обработчик события добавления бота в группу
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_chat_members))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
