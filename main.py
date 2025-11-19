import os
import logging
import re

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

OWNER_ID = 407368838  # твой основной аккаунт @Sergey_Anashkin

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ================= СОСТОЯНИЯ ДИАЛОГА =================

(
    CONTACT_NAME,
    CONTACT_PHONE,
    CONTACT_QUESTION,
    CONTACT_TIME,
    CONTACT_METHOD,
    CONTACT_REVIEW,
) = range(6)

# ================= КЛАВИАТУРЫ =================

MAIN_MENU = ReplyKeyboardMarkup(
    [
        [KeyboardButton("👶 Планируем / ждём ребёнка")],
        [KeyboardButton("🩺 Я врач")],
        [KeyboardButton("📅 Записаться / Оставить контакты")],
        [KeyboardButton("❓ FAQ")],
    ],
    resize_keyboard=True,
)

BACK_CANCEL_KB = ReplyKeyboardMarkup(
    [
        [KeyboardButton("⬅️ Назад"), KeyboardButton("Отменить")],
    ],
    resize_keyboard=True,
)

def make_time_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["📞 Сейчас", "Сегодня 14–18"],
            ["Сегодня 18–21", "Завтра"],
            ["Напишу свой вариант"],
            ["⬅️ Назад", "Отменить"],
        ],
        resize_keyboard=True,
    )

def make_method_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["📞 Звонок"],
            ["💬 Telegram"],
            ["📱 WhatsApp"],
            ["⬅️ Назад", "Отменить"],
        ],
        resize_keyboard=True,
    )

def make_review_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["✅ Всё верно, отправить"],
            ["✏️ Изменить имя", "✏️ Изменить телефон"],
            ["✏️ Изменить вопрос"],
            ["✏️ Изменить время", "✏️ Изменить способ связи"],
            ["Отменить"],
        ],
        resize_keyboard=True,
    )

# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================

def is_cancel(text: str) -> bool:
    if not text:
        return False
    t = text.strip().lower()
    return t in ("отменить", "отмена", "cancel", "stop", "quit")

def is_back(text: str) -> bool:
    if not text:
        return False
    t = text.strip().lower()
    return t in ("⬅️ назад", "назад", "back", "go back")

def normalize_phone(phone: str) -> str:
    return phone.strip()

def phone_looks_ok(phone: str) -> bool:
    # очень мягкая проверка: цифры, +, -, пробелы, скобки; длина 6–20
    return bool(re.match(r"^[\d\+\-\s\(\)]{6,20}$", phone.strip()))

async def notify_owner_text(bot, text: str):
    try:
        await bot.send_message(chat_id=OWNER_ID, text=text)
    except Exception as e:
        logger.warning("Не удалось отправить сообщение владельцу: %s", e)

# ================= /start и простые разделы =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info("User %s (%s) used /start", user.id, user.username)
    await update.message.reply_text(
        "Привет! 👋\n\n"
        "Я бот проекта «Скрининг на носительство».\n"
        "Помогаю будущим родителям и врачам разобраться в генетических исследованиях.\n\n"
        "Выберите, что вам ближе:",
        reply_markup=MAIN_MENU,
    )

async def main_menu_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вы в главном меню. Выберите раздел:",
        reply_markup=MAIN_MENU,
    )

async def planning_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Раздел для тех, кто планирует или ждёт ребёнка 👶\n\n"
        "Скрининг на носительство помогает заранее понять риск наследственных "
        "заболеваний у будущего ребёнка.\n\n"
        "Если хотите, можете оставить свои контакты — нажмите «📅 Записаться / Оставить контакты».",
        reply_markup=MAIN_MENU,
    )

async def doctor_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Раздел для врачей 👩‍⚕️👨‍⚕️\n\n"
        "Если вы хотите рекомендовать пациентам скрининг на носительство и другие "
        "генетические исследования, оставьте контакты через «📅 Записаться / Оставить контакты», "
        "укажите, что вы врач, и формат сотрудничества, который вам интересен.",
        reply_markup=MAIN_MENU,
    )

async def faq_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "❓ *FAQ по скринингу на носительство*\n\n"
        "1️⃣ *Кому это нужно?*\n"
        "Парам, которые планируют беременность или ЭКО, а также тем, у кого в семье были "
        "случаи тяжёлых наследственных заболеваний.\n\n"
        "2️⃣ *Когда лучше делать скрининг?*\n"
        "Идеально — ДО наступления беременности. Но и во время беременности он тоже может быть полезен.\n\n"
        "3️⃣ *Что показывает анализ?*\n"
        "Являются ли вы и/или партнёр носителями мутаций, которые повышают риск рождения ребёнка "
        "с тяжёлым наследственным заболеванием.\n\n"
        "4️⃣ *Если мы оба носители, что дальше?*\n"
        "Риск выше, но это не приговор. Есть варианты: ЭКО с ПГТ, донорский материал, "
        "другие репродуктивные решения. Всё обсуждается с врачом-генетиком.\n\n"
        "Если хотите конкретики по вашей ситуации — оставьте контакты, и с вами свяжутся.",
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=MAIN_MENU)

# ================= ДИАЛОГ «ОСТАВИТЬ КОНТАКТЫ» =================

async def contacts_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Старт диалога по кнопке '📅 Записаться / Оставить контакты'."""
    user = update.effective_user
    context.user_data["lead"] = {
        "name": None,
        "phone": None,
        "question": None,
        "time": None,
        "method": None,
    }
    context.user_data.pop("edit_field", None)

    await notify_owner_text(
        context.bot,
        f"👣 Пользователь зашёл в раздел «Оставить контакты»\n\n"
        f"Имя: {user.full_name}\n"
        f"ID: {user.id}\n"
        f"Username: @{user.username or '—'}",
    )

    suggested_name = user.full_name or "Например: Иван Иванов"
    await update.message.reply_text(
        f"Давайте аккуратно соберём ваши данные, чтобы мы могли с вами связаться.\n\n"
        f"1️⃣ Как к вам обращаться?\n"
        f"(можно как в Telegram: {suggested_name})",
        reply_markup=ReplyKeyboardMarkup(
            [["Отменить"]],
            resize_keyboard=True,
        ),
    )
    return CONTACT_NAME

async def contacts_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("lead", None)
    context.user_data.pop("edit_field", None)
    await update.message.reply_text(
        "Запись отменена. Вы в главном меню.",
        reply_markup=MAIN_MENU,
    )
    return ConversationHandler.END

# --- Имя ---

async def contacts_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text or ""
    if is_cancel(text):
        return await contacts_cancel(update, context)

    lead = context.user_data.get("lead", {})
    lead["name"] = text.strip() or lead.get("name")

    # если это редактирование
    if context.user_data.get("edit_field") == "name":
        context.user_data["edit_field"] = None
        return await contacts_review(update, context)

    await update.message.reply_text(
        "2️⃣ Напишите, пожалуйста, *номер телефона* для связи:",
        parse_mode="Markdown",
        reply_markup=BACK_CANCEL_KB,
    )
    return CONTACT_PHONE

# --- Телефон ---

async def contacts_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text or ""
    if is_cancel(text):
        return await contacts_cancel(update, context)
    if is_back(text):
        # вернуться к имени
        await update.message.reply_text(
            "Изменим имя.\nПожалуйста, отправьте, как к вам обращаться:",
            reply_markup=ReplyKeyboardMarkup(
                [["Отменить"]],
                resize_keyboard=True,
            ),
        )
        context.user_data["edit_field"] = "name"
        return CONTACT_NAME

    phone = normalize_phone(text)
    if not phone_looks_ok(phone):
        await update.message.reply_text(
            "Похоже, номер указан в необычном формате 😅\n"
            "Отправьте, пожалуйста, номер телефона ещё раз (можно с +7, пробелами и скобками).",
            reply_markup=BACK_CANCEL_KB,
        )
        return CONTACT_PHONE

    lead = context.user_data.get("lead", {})
    lead["phone"] = phone

    if context.user_data.get("edit_field") == "phone":
        context.user_data["edit_field"] = None
        return await contacts_review(update, context)

    await update.message.reply_text(
        "3️⃣ Кратко опишите, *какой у вас вопрос?*\n"
        "(например: планирование беременности, скрининг на носительство, консультация генетика)",
        parse_mode="Markdown",
        reply_markup=BACK_CANCEL_KB,
    )
    return CONTACT_QUESTION

# --- Вопрос ---

async def contacts_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text or ""
    if is_cancel(text):
        return await contacts_cancel(update, context)
    if is_back(text):
        # вернуться к телефону
        await update.message.reply_text(
            "Изменим телефон.\nОтправьте, пожалуйста, номер телефона для связи:",
            reply_markup=BACK_CANCEL_KB,
        )
        context.user_data["edit_field"] = "phone"
        return CONTACT_PHONE

    lead = context.user_data.get("lead", {})
    lead["question"] = text.strip() or lead.get("question")

    if context.user_data.get("edit_field") == "question":
        context.user_data["edit_field"] = None
        return await contacts_review(update, context)

    await update.message.reply_text(
        "4️⃣ Когда вам удобно поговорить?\n\n"
        "Выберите вариант или напишите свой:",
        reply_markup=make_time_keyboard(),
    )
    return CONTACT_TIME

# --- Время ---

async def contacts_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    if is_cancel(text):
        return await contacts_cancel(update, context)
    if is_back(text):
        # вернуться к вопросу
        await update.message.reply_text(
            "Изменим формулировку вопроса.\n\n"
            "Кратко опишите, пожалуйста, ваш вопрос или ситуацию:",
            reply_markup=BACK_CANCEL_KB,
        )
        context.user_data["edit_field"] = "question"
        return CONTACT_QUESTION

    if text == "Напишу свой вариант":
        await update.message.reply_text(
            "Укажите удобное время для связи в свободной форме:",
            reply_markup=BACK_CANCEL_KB,
        )
        return CONTACT_TIME

    lead = context.user_data.get("lead", {})
    lead["time"] = text or lead.get("time")

    if context.user_data.get("edit_field") == "time":
        context.user_data["edit_field"] = None
        return await contacts_review(update, context)

    await update.message.reply_text(
        "5️⃣ Как удобнее с вами связаться?",
        reply_markup=make_method_keyboard(),
    )
    return CONTACT_METHOD

# --- Способ связи ---

async def contacts_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    if is_cancel(text):
        return await contacts_cancel(update, context)
    if is_back(text):
        # вернуться к времени
        await update.message.reply_text(
            "Изменим удобное время.\n\n"
            "Когда вам удобно поговорить?",
            reply_markup=make_time_keyboard(),
        )
        context.user_data["edit_field"] = "time"
        return CONTACT_TIME

    lead = context.user_data.get("lead", {})
    lead["method"] = text or lead.get("method")

    # переходим к экрану проверки
    return await contacts_review(update, context)

# --- Экран проверки и возможность редактировать ---

async def contacts_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lead = context.user_data.get("lead", {})
    user = update.effective_user

    review_text = (
        "Проверьте, пожалуйста, данные перед отправкой:\n\n"
        f"👤 Имя: {lead.get('name', '—')}\n"
        f"📞 Телефон: {lead.get('phone', '—')}\n"
        f"💬 Вопрос: {lead.get('question', '—')}\n"
        f"⏰ Удобное время: {lead.get('time', '—')}\n"
        f"📱 Способ связи: {lead.get('method', '—')}\n\n"
        "Если всё верно — нажмите «✅ Всё верно, отправить».\n"
        "Если хотите что-то исправить — выберите, что именно."
    )

    await update.message.reply_text(
        review_text,
        reply_markup=make_review_keyboard(),
    )
    return CONTACT_REVIEW

async def contacts_review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    lead = context.user_data.get("lead", {})
    user = update.effective_user

    if is_cancel(text):
        return await contacts_cancel(update, context)

    if text == "✅ Всё верно, отправить":
        # отправляем заявку владельцу
        msg = (
            "📩 *НОВАЯ ЗАЯВКА ОТ ПОЛЬЗОВАТЕЛЯ*\n\n"
            f"👤 *Имя:* {lead.get('name', '—')}\n"
            f"📞 *Телефон:* {lead.get('phone', '—')}\n"
            f"💬 *Вопрос:* {lead.get('question', '—')}\n"
            f"⏰ *Удобное время:* {lead.get('time', '—')}\n"
            f"📱 *Способ связи:* {lead.get('method', '—')}\n\n"
            f"👤 Telegram: @{user.username or '—'}\n"
            f"🆔 ID: {user.id}"
        )
        try:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=msg,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error("Не удалось отправить заявку владельцу: %s", e)

        await update.message.reply_text(
            "Спасибо! Ваша заявка отправлена.\n"
            "Мы свяжемся с вами, как только появится возможность.",
            reply_markup=MAIN_MENU,
        )
        context.user_data.pop("lead", None)
        context.user_data.pop("edit_field", None)
        return ConversationHandler.END

    # редактирование полей
    mapping = {
        "✏️ Изменить имя": "name",
        "✏️ Изменить телефон": "phone",
        "✏️ Изменить вопрос": "question",
        "✏️ Изменить время": "time",
        "✏️ Изменить способ связи": "method",
    }
    field = mapping.get(text)
    if field == "name":
        context.user_data["edit_field"] = "name"
        await update.message.reply_text(
            "Введите новое имя:",
            reply_markup=ReplyKeyboardMarkup([["Отменить"]], resize_keyboard=True),
        )
        return CONTACT_NAME
    elif field == "phone":
        context.user_data["edit_field"] = "phone"
        await update.message.reply_text(
            "Введите новый номер телефона:",
            reply_markup=BACK_CANCEL_KB,
        )
        return CONTACT_PHONE
    elif field == "question":
        context.user_data["edit_field"] = "question"
        await update.message.reply_text(
            "Сформулируйте вопрос ещё раз:",
            reply_markup=BACK_CANCEL_KB,
        )
        return CONTACT_QUESTION
    elif field == "time":
        context.user_data["edit_field"] = "time"
        await update.message.reply_text(
            "Укажите удобное время для связи:",
            reply_markup=make_time_keyboard(),
        )
        return CONTACT_TIME
    elif field == "method":
        context.user_data["edit_field"] = "method"
        await update.message.reply_text(
            "Выберите удобный способ связи:",
            reply_markup=make_method_keyboard(),
        )
        return CONTACT_METHOD

    # если ввели что-то странное на этапе проверки — просто покажем ещё раз
    return await contacts_review(update, context)

# ================= ОБЩИЙ ХЕНДЛЕР ТЕКСТА ВНЕ ДИАЛОГА =================

async def fallback_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Всё, что не поймал ConversationHandler и не попало в кнопки
    await update.message.reply_text(
        "Принял 👍\n"
        "Чтобы вернуться в меню, нажмите /start\n"
        "Чтобы оставить контакты, используйте кнопку «📅 Записаться / Оставить контакты».",
        reply_markup=MAIN_MENU,
    )

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Простые разделы
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^⬅️ Назад в меню$"), main_menu_entry))
    app.add_handler(MessageHandler(filters.Regex("^👶 Планируем / ждём ребёнка$"), planning_entry))
    app.add_handler(MessageHandler(filters.Regex("^🩺 Я врач$"), doctor_entry))
    app.add_handler(MessageHandler(filters.Regex("^❓ FAQ$"), faq_entry))

    # Диалог «Оставить контакты»
    contact_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📅 Записаться / Оставить контакты$"), contacts_start)
        ],
        states={
            CONTACT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contacts_name),
            ],
            CONTACT_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contacts_phone),
            ],
            CONTACT_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contacts_question),
            ],
            CONTACT_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contacts_time),
            ],
            CONTACT_METHOD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contacts_method),
            ],
            CONTACT_REVIEW: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contacts_review_handler),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^(Отменить|Cancel)$"), contacts_cancel),
        ],
        name="contacts_conversation",
        persistent=False,
    )
    app.add_handler(contact_conv)

    # Всё остальное текстовое — в общий обработчик
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text))

    print("Бот запущен.")
    app.run_polling()


if __name__ == "__main__":
    main()
