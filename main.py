import os
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
    ConversationHandler,
    ContextTypes,
    filters,
)

# ================= НАСТРОЙКИ =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не задана")

# твой основной аккаунт, куда прилетают заявки
OWNER_ID = 407368838  # @Sergey_Anashkin

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ================= КЛАВИАТУРЫ =================

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["🍼 Планируем / ждём ребёнка"],
        ["👨‍⚕️ Я врач"],
        ["❓ Что такое скрининг на носительство?"],
    ],
    resize_keyboard=True,
)

PLANNING_MENU = ReplyKeyboardMarkup(
    [
        ["📄 Получить памятку"],
        ["✍️ Записаться / Оставить контакты"],
        ["⬅️ Назад в меню"],
    ],
    resize_keyboard=True,
)

BACK_TO_MENU_KB = ReplyKeyboardMarkup(
    [
        ["⬅️ Назад в меню"],
    ],
    resize_keyboard=True,
)

# ================== СТЕЙТЫ ДЛЯ DIALOG FLOW ==================

(
    CONTACT_NAME,
    CONTACT_CITY,
    CONTACT_CONTACT,
    CONTACT_QUESTION,
) = range(4)

# ================ ОБЫЧНЫЕ ХЕНДЛЕРЫ ==================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Стартовое сообщение и главное меню."""
    user = update.effective_user
    text = (
        "Привет!\n"
        "Это бот проекта «Скрининг на носительство» — про ответственный подход "
        "к рождению детей.\n\n"
        "Выберите раздел:"
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)
    logger.info("User %s (%s) used /start", user.id, user.username)


async def main_menu_entry(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Возврат в главное меню по кнопке."""
    await update.message.reply_text("Вы в главном меню. Выберите раздел:", reply_markup=MAIN_MENU)


async def planning_entry(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Раздел для тех, кто планирует / ждёт ребёнка."""
    text = (
        "Отвечаем честно:\n"
        "• Были ли тяжёлые наследственные заболевания в семье?\n"
        "• Планируете беременность / ЭКО?\n"
        "• Есть ли ребёнок с генетическим заболеванием?\n\n"
        "Даже при спокойной семейной истории скрининг делают как элемент "
        "ответственного планирования.\n\n"
        "Здесь вы можете:\n"
        "• 📄 получить памятку\n"
        "• ✍️ оставить контакты и вопрос\n"
    )
    await update.message.reply_text(text, reply_markup=PLANNING_MENU)


async def doctor_entry(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Раздел для врачей."""
    text = (
        "Раздел для врачей.\n\n"
        "Если вы хотите рекомендовать пациентам скрининг на носительство и другие "
        "генетические исследования, напишите, и я свяжусь с вами лично."
    )
    await update.message.reply_text(text, reply_markup=BACK_TO_MENU_KB)


async def faq_entry(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Краткий FAQ — что такое скрининг на носительство."""
    text = (
        "Скрининг на носительство — это анализ ДНК здоровых людей, который показывает, "
        "являются ли они носителями наследственных заболеваний.\n\n"
        "Зачем это нужно:\n"
        "• оценить риски для будущих детей,\n"
        "• вовремя предложить паре расширенные обследования,\n"
        "• принять более осознанные решения при планировании беременности.\n\n"
        "Если хотите поговорить подробно — нажмите «Планируем / ждём ребёнка» "
        "и выберите «Записаться / Оставить контакты»."
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)


async def send_memo(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Заглушка под памятку (ссылку можно будет заменить)."""
    text = (
        "Скоро здесь появится ссылка на памятку для пациентов.\n\n"
        "А пока можете задать свой вопрос через раздел «Записаться / Оставить контакты»."
    )
    await update.message.reply_text(text, reply_markup=PLANNING_MENU)


# ============== ДИАЛОГ СБОРА КОНТАКТОВ ==============


async def contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Старт диалога — пользователь выбрал 'Записаться / Оставить контакты'."""
    user = update.effective_user

    # Уведомим владельца, что человек зашёл в раздел записи
    notify_text = (
        "👣 Пользователь зашёл в раздел: «Записаться / Оставить контакты»\n\n"
        f"Имя: {user.full_name}\n"
        f"ID: {user.id}\n"
        f"Username: @{user.username if user.username else '—'}"
    )
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=notify_text)
    except Exception as e:
        logger.warning("Не удалось отправить служебное сообщение владельцу: %s", e)

    context.user_data["lead"] = {}

    suggested_name = user.full_name if user and user.full_name else "Например: Иван Иванов"
    text = (
        "Давайте я аккуратно соберу ваши данные, чтобы я или врач могли с вами связаться.\n\n"
        f"1️⃣ Как к вам обращаться?\n"
        f"(можно как в Telegram: {suggested_name})"
    )
    await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup([["Отменить"]], resize_keyboard=True))
    return CONTACT_NAME


async def contact_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем имя."""
    name = update.message.text.strip()
    if not name or name.lower() == "отменить":
        await update.message.reply_text("Запись отменена. Вы в главном меню.", reply_markup=MAIN_MENU)
        return ConversationHandler.END

    context.user_data["lead"]["name"] = name

    text = "2️⃣ Из какого вы города?"
    await update.message.reply_text(text)
    return CONTACT_CITY


async def contact_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем город."""
    city = update.message.text.strip()
    if not city or city.lower() == "отменить":
        await update.message.reply_text("Запись отменена. Вы в главном меню.", reply_markup=MAIN_MENU)
        return ConversationHandler.END

    context.user_data["lead"]["city"] = city

    # Клавиатура для запроса контакта
    kb = ReplyKeyboardMarkup(
        [
            [KeyboardButton("📱 Отправить мой номер телефона", request_contact=True)],
            ["Написать контакт вручную"],
            ["Отменить"],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    text = (
        "3️⃣ Как с вами лучше связаться?\n"
        "Вы можете:\n"
        "• нажать «📱 Отправить мой номер телефона»,\n"
        "• или выбрать «Написать контакт вручную» и отправить телефон / e-mail / @username."
    )
    await update.message.reply_text(text, reply_markup=kb)
    return CONTACT_CONTACT


async def contact_contact_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Контакт пришёл кнопкой с номером телефона."""
    contact = update.message.contact
    number = contact.phone_number
    context.user_data["lead"]["contact"] = f"Телефон (кнопкой): {number}"

    text = "4️⃣ Кратко опишите ваш вопрос или ситуацию. Можно в свободной форме."
    await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup([["Отменить"]], resize_keyboard=True))
    return CONTACT_QUESTION


async def contact_contact_manual(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Пользователь выбрал ввод контакта вручную или просто написал текст."""
    text_value = update.message.text.strip()

    if text_value.lower() == "отменить":
        await update.message.reply_text("Запись отменена. Вы в главном меню.", reply_markup=MAIN_MENU)
        return ConversationHandler.END

    if text_value == "Написать контакт вручную":
        await update.message.reply_text(
            "Пожалуйста, отправьте контакт одним сообщением: телефон, e-mail или @username.",
        )
        return CONTACT_CONTACT

    # это уже собственно контакт
    context.user_data["lead"]["contact"] = text_value

    text = "4️⃣ Кратко опишите ваш вопрос или ситуацию. Можно в свободной форме."
    await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup([["Отменить"]], resize_keyboard=True))
    return CONTACT_QUESTION


async def contact_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем вопрос и завершаем диалог."""
    question = update.message.text.strip()
    if not question or question.lower() == "отменить":
        await update.message.reply_text("Запись отменена. Вы в главном меню.", reply_markup=MAIN_MENU)
        return ConversationHandler.END

    context.user_data["lead"]["question"] = question

    user = update.effective_user
    lead = context.user_data.get("lead", {})

    # ------- отправляем заявку владельцу -------
    admin_text = (
        "📩 НОВАЯ ЗАЯВКА ОТ ПОЛЬЗОВАТЕЛЯ\n\n"
        f"👤 Имя: {lead.get('name', '—')}\n"
        f"🏙 Город: {lead.get('city', '—')}\n"
        f"📞 Контакт: {lead.get('contact', '—')}\n"
        f"📝 Вопрос: {lead.get('question', '—')}\n\n"
        f"Telegram ID: {user.id}\n"
        f"Username: @{user.username if user.username else '—'}"
    )

    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=admin_text)
    except Exception as e:
        logger.error("Не удалось отправить заявку владельцу: %s", e)

    # ------- отвечаем пользователю -------
    await update.message.reply_text(
        "Спасибо! Ваша заявка отправлена.\n"
        "Я или врач свяжемся с вами, как только появится возможность.",
        reply_markup=MAIN_MENU,
    )

    # очищаем временные данные
    context.user_data.pop("lead", None)
    return ConversationHandler.END


async def contact_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена диалога по /cancel или кнопке."""
    context.user_data.pop("lead", None)
    await update.message.reply_text("Запись отменена. Вы в главном меню.", reply_markup=MAIN_MENU)
    return ConversationHandler.END


# ================== MAIN ==================


def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # --- обычные хендлеры ---
    application.add_handler(CommandHandler("start", start))

    application.add_handler(
        MessageHandler(filters.Regex("^⬅️ Назад в меню$"), main_menu_entry)
    )
    application.add_handler(
        MessageHandler(filters.Regex("^🍼 Планируем / ждём ребёнка$"), planning_entry)
    )
    application.add_handler(
        MessageHandler(filters.Regex("^👨‍⚕️ Я врач$"), doctor_entry)
    )
    application.add_handler(
        MessageHandler(filters.Regex("^❓ Что такое скрининг на носительство\\?$"), faq_entry)
    )
    application.add_handler(
        MessageHandler(filters.Regex("^📄 Получить памятку$"), send_memo)
    )

    # --- диалог по сбору контактов ---
    contact_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^✍️ Записаться / Оставить контакты$"), contact_start)
        ],
        states={
            CONTACT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contact_name)
            ],
            CONTACT_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contact_city)
            ],
            CONTACT_CONTACT: [
                MessageHandler(filters.CONTACT, contact_contact_from_button),
                MessageHandler(filters.TEXT & ~filters.COMMAND, contact_contact_manual),
            ],
            CONTACT_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contact_question)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", contact_cancel),
            MessageHandler(filters.Regex("^Отменить$"), contact_cancel),
        ],
        name="contact_conversation",
        persistent=False,
    )

    application.add_handler(contact_conv)

    # Запуск
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
