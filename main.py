import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ===== НАСТРОЙКИ =====
TELEGRAM_BOT_TOKEN = "8280033631:AAEMluh1pe9T7wPAZ40tLhrck6tzHjJlsFU"
OWNER_ID = 407368838  # @Sergey_Anashkin

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

USER_STATE = {}

MAIN_MENU = ReplyKeyboardMarkup(
    [
        [KeyboardButton("👶 Планируем / ждём ребёнка")],
        [KeyboardButton("🩺 Я врач")],
        [KeyboardButton("❓ Что такое скрининг на носительство?")],
    ],
    resize_keyboard=True,
)


# ===== Команда /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    USER_STATE[uid] = "MAIN"

    text = (
        "Привет!\n"
        "Я бот проекта «Скрининг на носительство» — про ответственный подход к рождению детей.\n\n"
        "Чем могу помочь?"
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)


# ===== Отправка уведомления владельцу =====
async def notify_owner(update: Update):
    """Пересылаем тебе все текстовые сообщения клиентов."""
    user = update.effective_user
    await update.get_bot().send_message(
        chat_id=OWNER_ID,
        text=(
            f"💬 Новое сообщение от пользователя:\n\n"
            f"👤 Имя: {user.full_name}\n"
            f"🆔 ID: {user.id}\n\n"
            f"Текст:\n{update.message.text}"
        )
    )


# ===== Обработка текста =====
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_owner(update)

    msg = update.message.text

    if msg == "👶 Планируем / ждём ребёнка":
        await update.message.reply_text(
            "Отвечайте честно:\n\n"
            "▫️ Были ли тяжёлые наследственные заболевания в семье?\n"
            "▫️ Планируете беременность / ЭКО?\n"
            "▫️ Есть ли ребёнок с генетическим заболеванием?\n\n"
            "Даже при спокойной семейной истории семейные пары делают скрининг как элемент ответственного планирования."
        )
        return

    if msg == "🩺 Я врач":
        await update.message.reply_text(
            "Формат для врачей:\n\n"
            "⬜ создаём уникальный промокод,\n"
            "⬜ пациент получает 3% скидки,\n"
            "⬜ кейсы привязываются к вам,\n"
            "⬜ вы получаете агентское вознаграждение.\n\n"
            "Что дальше?"
        )
        return

    if msg == "❓ Что такое скрининг на носительство?":
        await update.message.reply_text(
            "Скрининг на носительство — это анализ, который помогает ДО беременности "
            "понять риск рождения ребёнка с тяжёлым наследственным заболеванием."
        )
        return

    await update.message.reply_text(
        "Принято 👍\nЕсли хотите вернуться — нажмите /start"
    )


# ===== Запуск =====
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
