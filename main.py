import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

# Получаем токен из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")


# --- Команды бота ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот работает. Чем могу помочь?")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Это бот для проекта Carrier Screening. Я на связи!")


# --- Главная функция ---
def main():
    if TOKEN is None:
        raise RuntimeError("Ошибка: переменная окружения BOT_TOKEN не установлена!")

    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрация команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Запуск бота
    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
