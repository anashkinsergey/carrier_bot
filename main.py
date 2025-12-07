import os
import re
import logging
from typing import Dict, Any, List

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ---------------------------------------------------------------------
# ЛОГИРОВАНИЕ
# ---------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logger.info("🚀 Bot started: carrier_screening_bot")


# ---------------------------------------------------------------------
# НАСТРОЙКИ
# ---------------------------------------------------------------------

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "0"))

(
    CONTACT_NAME,
    CONTACT_PHONE,
    CONTACT_CHOICE,
    CONTACT_QUESTION,
    CONTACT_TIME,
    CONTACT_METHOD,
    CONTACT_CONFIRM,
) = range(7)


# ---------------------------------------------------------------------
# I18N
# ---------------------------------------------------------------------

def get_lang(update: Update) -> str:
    user = update.effective_user
    code = (user.language_code or "").lower() if user else ""
    return "ru" if code.startswith("ru") else "en"


def t(label: str, lang: str = "ru") -> str:
    texts = {
        "greeting": {
            "ru": (
                "Привет! Я бот по скринингу на носительство наследственных заболеваний.\n\n"
                "Чем могу помочь?"
            ),
            "en": "Hi! How can I help you?",
        },
        "main_menu_title": {"ru": "Выберите раздел:", "en": "Choose a section:"},

        "btn_plan": {"ru": "👶 Планируем / ждём ребёнка", "en": "Planning"},
        "btn_doctor": {"ru": "👨‍⚕️ Я врач", "en": "Doctor"},
        "btn_contact": {"ru": "📝 Записаться / Оставить контакты", "en": "Contacts"},
        "btn_faq": {"ru": "❓ FAQ", "en": "FAQ"},
        "btn_back": {"ru": "⬅️ Назад", "en": "Back"},
        "btn_cancel": {"ru": "❌ Отмена", "en": "Cancel"},

        "name_ask": {
            "ru": "Как к вам обращаться?",
            "en": "How should I call you?",
        },

        "phone_choice": {
            "ru": "Как удобнее оставить контакт?",
            "en": "Choose your contact method:",
        },

        "choice_phone": {"ru": "📱 Отправить номер", "en": "📱 Send phone"},
        "choice_username": {"ru": "🆔 Оставить username", "en": "🆔 Use username"},
        "choice_other": {"ru": "✏️ Указать другой контакт", "en": "✏️ Other contact"},

        "phone_ask": {
            "ru": "Отправьте номер телефона:",
            "en": "Send your phone:",
        },
        "phone_invalid": {
            "ru": "Похоже, номер в непривычном формате. Пример: +7 999 123-45-67",
            "en": "Phone looks invalid. Example: +1 202 555 0199",
        },

        "other_contact_ask": {
            "ru": "Напишите удобный способ связи:",
            "en": "Write your preferred contact method:",
        },

        "question_ask": {
            "ru": "Кратко опишите вопрос:",
            "en": "Describe your question:",
        },

        "time_ask": {
            "ru": "Когда удобно поговорить?",
            "en": "When can we contact you?",
        },

        "method_ask": {
            "ru": "Как удобнее связаться?",
            "en": "Preferred contact method:",
        },

        "contact_canceled": {
            "ru": "Заявка отменена.",
            "en": "Request cancelled.",
        },

        "contact_summary": {
            "ru": "Проверьте данные:\n",
            "en": "Check your data:\n",
        },

        "summary_name": {"ru": "Имя", "en": "Name"},
        "summary_phone": {"ru": "Контакт", "en": "Contact"},
        "summary_question": {"ru": "Вопрос", "en": "Question"},
        "summary_time": {"ru": "Время", "en": "Time"},
        "summary_method": {"ru": "Способ связи", "en": "Method"},

        "confirm_ask": {
            "ru": "Отправляем заявку?",
            "en": "Send request?",
        },

        "btn_confirm_send": {"ru": "✅ Отправить", "en": "Send"},
        "btn_confirm_edit": {"ru": "✏️ Изменить", "en": "Edit"},
        "btn_confirm_cancel": {"ru": "❌ Отмена", "en": "Cancel"},

        "lead_sent_user": {
            "ru": "Готово! Заявка отправлена.",
            "en": "Your request has been sent.",
        },

        "lead_sent_owner_title": {
            "ru": "📬 Новая заявка",
            "en": "New Lead",
        },

        "unknown_command": {
            "ru": "Используйте кнопки меню.",
            "en": "Use menu buttons.",
        },
    }
    return texts.get(label, {}).get(lang, text)


# ---------------------------------------------------------------------
# ВАЛИДАЦИЯ
# ---------------------------------------------------------------------

def is_valid_phone(phone: str) -> bool:
    cleaned = re.sub(r"[^\d+]", "", phone).strip()
    if not cleaned.startswith("+"):
        return False
    digits = re.findall(r"\d", cleaned)
    return 10 <= len(digits) <= 15


# ---------------------------------------------------------------------
# КЛАВИАТУРЫ
# ---------------------------------------------------------------------

def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t("btn_plan", lang)],
            [t("btn_doctor", lang)],
            [t("btn_contact", lang)],
            [t("btn_faq", lang)],
        ],
        resize_keyboard=True,
    )


def back_cancel_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t("btn_back", lang), t("btn_cancel", lang)],
        ],
        resize_keyboard=True,
    )


# ---------------------------------------------------------------------
# START
# ---------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.message.reply_text(t("greeting", lang),
                                    reply_markup=main_menu_keyboard(lang))


# ---------------------------------------------------------------------
# МЕНЮ
# ---------------------------------------------------------------------

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = update.message.text.strip()

    if text == t("btn_contact", lang):
        return await contact_start(update, context)

    await update.message.reply_text(
        t("unknown_command", lang),
        reply_markup=main_menu_keyboard(lang),
    )


# ---------------------------------------------------------------------
# КОНТАКТНАЯ ФОРМА (НОВАЯ ЛОГИКА)
# ---------------------------------------------------------------------

async def contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)

    context.user_data["lang"] = lang
    context.user_data["lead"] = {}

    await update.message.reply_text(
        t("name_ask", lang),
        reply_markup=ReplyKeyboardMarkup(
            [[t("btn_cancel", lang)]],
            resize_keyboard=True,
        ),
    )
    return CONTACT_NAME


async def contact_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    txt = update.message.text.strip()

    if txt == t("btn_cancel", lang):
        return await cancel_contact(update)

    context.user_data["lead"]["name"] = txt

    kb = ReplyKeyboardMarkup(
        [
            [t("choice_phone", lang)],
            [t("choice_username", lang)],
            [t("choice_other", lang)],
            [t("btn_cancel", lang)],
        ],
        resize_keyboard=True,
    )

    await update.message.reply_text(
        t("phone_choice", lang),
        reply_markup=kb,
    )
    return CONTACT_CHOICE


async def contact_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    choice = update.message.text.strip()

    if choice == t("btn_cancel", lang):
        return await cancel_contact(update)

    # Вариант 1: Отправить номер
    if choice == t("choice_phone", lang):
        kb = ReplyKeyboardMarkup(
            [
                [KeyboardButton("📱 Отправить номер", request_contact=True)],
                [t("btn_back", lang), t("btn_cancel", lang)],
            ],
            resize_keyboard=True,
        )
        await update.message.reply_text(t("phone_ask", lang), reply_markup=kb)
        return CONTACT_PHONE

    # Вариант 2: Оставить username
    if choice == t("choice_username", lang):
        user = update.effective_user
        username = f"@{user.username}" if user.username else "—"
        context.user_data["lead"]["phone"] = username

        await update.message.reply_text(
            t("question_ask", lang),
            reply_markup=back_cancel_keyboard(lang),
        )
        return CONTACT_QUESTION

    # Вариант 3: Указать другой контакт
    if choice == t("choice_other", lang):
        await update.message.reply_text(
            t("other_contact_ask", lang),
            reply_markup=back_cancel_keyboard(lang),
        )
        return CONTACT_PHONE

    return CONTACT_CHOICE


async def contact_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]

    # Если контакт отправлен через Telegram-кнопку
    if update.message.contact:
        raw = update.message.contact.phone_number
        phone = raw.strip()
    else:
        phone = update.message.text.strip()

        if phone == t("btn_cancel", lang):
            return await cancel_contact(update)
        if phone == t("btn_back", lang):
            return await contact_start(update, context)

    # Проверка, если пользователь вручную вводит номер
    if not update.message.contact:
        if not is_valid_phone(phone):
            await update.message.reply_text(
                t("phone_invalid", lang),
                reply_markup=back_cancel_keyboard(lang),
            )
            return CONTACT_PHONE

    context.user_data["lead"]["phone"] = phone

    await update.message.reply_text(
        t("question_ask", lang),
        reply_markup=back_cancel_keyboard(lang),
    )
    return CONTACT_QUESTION


async def contact_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    txt = update.message.text.strip()

    if txt == t("btn_cancel", lang):
        return await cancel_contact(update)
    if txt == t("btn_back", lang):
        return CONTACT_PHONE

    context.user_data["lead"]["question"] = txt

    kb = ReplyKeyboardMarkup(
        [
            ["Утром", "Днём"],
            ["Вечером", "Не принципиально"],
            [t("btn_back", lang), t("btn_cancel", lang)],
        ],
        resize_keyboard=True,
    )

    await update.message.reply_text(t("time_ask", lang), reply_markup=kb)
    return CONTACT_TIME


async def contact_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    txt = update.message.text.strip()

    if txt == t("btn_cancel", lang):
        return await cancel_contact(update)
    if txt == t("btn_back", lang):
        return CONTACT_QUESTION

    context.user_data["lead"]["time"] = txt

    kb = ReplyKeyboardMarkup(
        [
            ["📞 Звонок", "💬 Telegram"],
            ["💬 WhatsApp"],
            [t("btn_back", lang), t("btn_cancel", lang)],
        ],
        resize_keyboard=True,
    )

    await update.message.reply_text(
        t("method_ask", lang),
        reply_markup=kb,
    )
    return CONTACT_METHOD


async def contact_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    txt = update.message.text.strip()

    if txt == t("btn_cancel", lang):
        return await cancel_contact(update)
    if txt == t("btn_back", lang):
        return CONTACT_TIME

    context.user_data["lead"]["method"] = txt

    return await contact_summary(update, context)


async def contact_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    lead = context.user_data["lead"]

    lines = [
        t("contact_summary", lang),
        f"{t('summary_name', lang)}: {lead['name']}",
        f"{t('summary_phone', lang)}: {lead['phone']}",
        f"{t('summary_question', lang)}: {lead['question']}",
        f"{t('summary_time', lang)}: {lead['time']}",
        f"{t('summary_method', lang)}: {lead['method']}",
        "",
        t("confirm_ask", lang),
    ]

    kb = ReplyKeyboardMarkup(
        [
            [t("btn_confirm_send", lang)],
            [t("btn_confirm_edit", lang)],
            [t("btn_confirm_cancel", lang)],
        ],
        resize_keyboard=True,
    )

    await update.message.reply_text("\n".join(lines), reply_markup=kb)
    return CONTACT_CONFIRM


async def cancel_contact(update: Update):
    lang = get_lang(update)
    await update.message.reply_text(
        t("contact_canceled", lang),
        reply_markup=None,
    )
    return ConversationHandler.END


async def contact_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    txt = update.message.text.strip()

    if txt == t("btn_confirm_cancel", lang):
        return await cancel_contact(update)

    if txt == t("btn_confirm_edit", lang):
        return await contact_start(update, context)

    if txt == t("btn_confirm_send", lang):
        lead = context.user_data["lead"]
        await send_lead(update, lang, lead)

        await update.message.reply_text(
            t("lead_sent_user", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    return CONTACT_CONFIRM


async def send_lead(update: Update, lang: str, lead: Dict[str, Any]):
    if not OWNER_CHAT_ID:
        return

    user = update.effective_user

    lines = [
        t("lead_sent_owner_title", lang),
        "",
        f"{t('summary_name', lang)}: {lead['name']}",
        f"{t('summary_phone', lang)}: {lead['phone']}",
        f"{t('summary_question', lang)}: {lead['question']}",
        f"{t('summary_time', lang)}: {lead['time']}",
        f"{t('summary_method', lang)}: {lead['method']}",
        "",
        f"User ID: {user.id}",
        f"Username: @{user.username}" if user.username else "Username: —",
    ]

    await update.get_bot().send_message(OWNER_CHAT_ID, "\n".join(lines))


# ---------------------------------------------------------------------
# /reply — ответ пользователю от владельца
# ---------------------------------------------------------------------

async def cmd_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OWNER_CHAT_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("Форма: /reply USER_ID текст...")
        return

    user_id = context.args[0]
    text = " ".join(context.args[1:])

    try:
        await context.bot.send_message(chat_id=user_id, text=text)
        await update.message.reply_text("Отправлено.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан!")

    app = Application.builder().token(BOT_TOKEN).build()

    # команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", cmd_reply))

    # контактная форма
    contact_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r".*"), contact_start)],
        states={
            CONTACT_NAME: [MessageHandler(filters.TEXT, contact_name)],
            CONTACT_CHOICE: [MessageHandler(filters.TEXT, contact_choice)],
            CONTACT_PHONE: [MessageHandler(filters.ALL, contact_phone)],
            CONTACT_QUESTION: [MessageHandler(filters.TEXT, contact_question)],
            CONTACT_TIME: [MessageHandler(filters.TEXT, contact_time)],
            CONTACT_METHOD: [MessageHandler(filters.TEXT, contact_method)],
            CONTACT_CONFIRM: [MessageHandler(filters.TEXT, contact_confirm)],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    app.add_handler(contact_conv)

    # обработка прочих сообщений
    app.add_handler(MessageHandler(filters.TEXT, handle_main_menu))

    app.run_polling()


if __name__ == "__main__":
    main()
