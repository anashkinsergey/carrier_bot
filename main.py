
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
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logger.info("🚀 Bot started: carrier_screening_bot")


BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "0"))


def t(label: str, lang: str = "ru") -> str:
    texts = {
        "greeting": {
    "ru": (
        "Здесь можно спокойно разобраться, есть ли в вашей ситуации вопрос по генетике.\n\n"
        "Можно задать свой вопрос — коротко, как получается.\n"
        "Можно просто посмотреть варианты.\n"
        "Можно закрыть тему и вернуться позже.\n\n"
        "Важно: это не консультация и не запись к врачу."
    ),
},
        "main_menu_title": {"ru": "Выберите раздел:", "en": "Choose a section:"},
        "btn_plan": {"ru": "👶 Планируем / ждём ребёнка", "en": "👶 Planning / expecting a baby"},
        "btn_doctor": {"ru": "👨‍⚕️ Я врач", "en": "👨‍⚕️ I am a doctor"},
        "btn_contact": {"ru": "📝 Записаться / Оставить контакты", "en": "📝 Leave contacts / book a call"},
        "btn_free_question": {"ru": "/Написать свой вопрос", "en": "Write my question"},
        "btn_end_free": {
            "ru": "Закончить диалог / Вернуться к меню",
            "en": "End dialog / Back to menu",
        },
        "free_q_button_explain": {
            "ru": (
                "Можете просто написать здесь свой вопрос в одном или нескольких сообщениях.\n\n"
                "Это можно сделать без телефона и других контактов — я всё равно передам ваши сообщения врачу."
            ),
            "en": (
                "You can just type your question here in one or several messages.\n\n"
                "You don’t have to leave a phone or any contacts — I will still forward your messages to the doctor."
            ),
        },
        "free_q_user": {
            "ru": (
                "Я передал ваше сообщение. Можно продолжать писать здесь, в боте — ответы будут приходить в этот же чат."
            ),
            "en": (
                "I’ve forwarded your message. You can keep chatting here in this bot — replies will arrive in the same chat."
            ),
        },
        "free_q_owner_title": {
            "ru": "💬 Новое сообщение в боте (без заявки)",
            "en": "💬 New bot message (no lead form)",
        },
        "btn_faq": {"ru": "❓ FAQ", "en": "❓ FAQ"},
        "btn_back": {"ru": "⬅️ Назад", "en": "⬅️ Back"},
        "btn_cancel": {"ru": "❌ Отмена", "en": "❌ Cancel"},
        "name_ask": {
            "ru": "Как к вам обращаться? (имя или имя + фамилия)",
            "en": "How should I call you? (name or full name)",
        },
        "phone_ask": {
            "ru": "Напишите, пожалуйста, номер телефона для связи:",
            "en": "Please send your phone number (with country code):",
        },
        "phone_invalid": {
            "ru": (
                "Похоже, номер в неверном формате.\n\n"
                "Например: +7 999 123-45-67 или +44 20 1234 5678.\n"
                "Попробуйте ещё раз."
            ),
            "en": (
                "The number seems to be in the wrong format.\n\n"
                "For example: +1 212 555 1234.\n"
                "Please try again."
            ),
        },
        "contact_how_ask": {
            "ru": "Как вам удобнее продолжить общение?",
            "en": "How would you prefer to continue communication?",
        },
        "contact_how_phone": {
            "ru": "📞 Позвонить / написать в мессенджер",
            "en": "📞 Call / messenger",
        },
        "contact_how_telegram": {
            "ru": "💬 Написать в Telegram",
            "en": "💬 Message in Telegram",
        },
        "contact_how_other": {
            "ru": "✉️ Другая форма связи (email и т.п.)",
            "en": "✉️ Another way (email etc.)",
        },
        "comment_ask": {
            "ru": "Если хотите, кратко напишите, что для вас сейчас актуально (по желанию):",
            "en": "Optionally, write a short comment about your situation:",
        },
        "contact_done_user": {
            "ru": (
                "Спасибо! Я передал ваши данные.\n"
                "С вами свяжутся и помогут подобрать подходящий формат генетического исследования."
            ),
            "en": (
                "Thank you! I’ve passed your details on.\n"
                "We’ll contact you to help choose an appropriate genetic test."
            ),
        },
        "lead_sent_user": {
            "ru": "Готово! Я передал вашу заявку. С вами свяжутся в ближайшее время.",
            "en": "Done! Your request has been sent. We’ll contact you soon.",
        },
        "lead_sent_owner_title": {"ru": "📬 Новая заявка", "en": "📬 New Lead"},
        "unknown_command": {
            "ru": "Пока не знаю, что делать с этим. Используйте меню ниже.",
            "en": "I don’t know what to do with that. Use the menu below.",
        },
        "faq_menu_title": {
            "ru": "❓ *FAQ по скринингу на носительство*\n\nВыберите вопрос:",
            "en": "❓ *Carrier screening FAQ*\n\nChoose a question:",
        },
        "faq_doctor_title": {
            "ru": "👨‍⚕️ *FAQ для врачей*\n",
            "en": "👨‍⚕️ *Doctor FAQ*\n",
        },
        "doctor_intro": {
            "ru": (
                "\n"
                "Здесь собраны ответы на типичные вопросы врачей о тестах на носительство.\n"
                "Выберите интересующую тему:"
            ),
            "en": (
                "\n"
                "Here are answers to typical doctors’ questions about carrier screening.\n"
                "Choose a topic:"
            ),
        },
    }
    return texts[label].get(lang, texts[label]["ru"])


def get_lang(update: Update) -> str:
    user_lang = None
    if update.effective_user and update.effective_user.language_code:
        user_lang = update.effective_user.language_code
    if user_lang and user_lang.startswith("en"):
        return "en"
    return "ru"


def main_menu_keyboard(lang: str, free_mode: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [t("btn_plan", lang)],
        [t("btn_doctor", lang)],
        [t("btn_contact", lang), t("btn_free_question", lang)],
        [t("btn_faq", lang)],
    ]
    if free_mode:
        rows.append([t("btn_end_free", lang)])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def back_cancel_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[t("btn_back", lang), t("btn_cancel", lang)]],
        resize_keyboard=True,
    )


def is_back(txt: str, lang: str) -> bool:
    return txt == t("btn_back", lang)


def is_cancel(txt: str, lang: str) -> bool:
    return txt == t("btn_cancel", lang)


def is_valid_phone(phone: str) -> bool:
    cleaned = re.sub(r"[^\d+]", "", phone).strip()
    if not cleaned.startswith("+"):
        return False
    digits = re.findall(r"\d", cleaned)
    return 10 <= len(digits) <= 15


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.message.reply_text(
        t("greeting", lang),
        reply_markup=main_menu_keyboard(lang),
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    msg = update.message or update.callback_query.message
    await msg.reply_text(t("main_menu_title", lang), reply_markup=main_menu_keyboard(lang))


async def explain_free_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    context.user_data["free_mode"] = True
    await update.message.reply_text(
        t("free_q_button_explain", lang),
        reply_markup=main_menu_keyboard(lang, free_mode=True),
    )


async def forward_free_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not OWNER_CHAT_ID:
        return
    user = update.effective_user
    if user and user.id == OWNER_CHAT_ID:
        return
    if update.message.from_user and update.message.from_user.is_bot:
        return
    lang = get_lang(update)
    text = update.message.text or ""
    lines_out = [
        t("free_q_owner_title", lang),
        "",
        f"User ID: {user.id if user else '–'}",
        f"Username: @{user.username}" if getattr(user, "username", None) else "Username: –",
        f"Имя: {user.full_name}" if getattr(user, "full_name", None) else "",
        "",
        "Сообщение:",
        text,
    ]
    msg_text = "\n".join([ln for ln in lines_out if ln != ""])
    await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=msg_text)
    await update.message.reply_text(
        t("free_q_user", lang),
        reply_markup=main_menu_keyboard(lang, free_mode=True),
    )
    contact_keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📱 Оставить номер телефона", callback_data="free_contact_phone")],
            [InlineKeyboardButton("💬 Использовать мой @username", callback_data="free_contact_username")],
        ]
    )
    await update.message.reply_text(
        "Как оставить контакт?",
        reply_markup=contact_keyboard,
    )


async def free_contact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user
    lang = get_lang(update)
    if data == "free_contact_phone":
        kb = ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Отправить номер телефона", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await query.answer()
        await query.message.reply_text(
            "Нажмите кнопку ниже, чтобы отправить номер телефона:",
            reply_markup=kb,
        )
        return
    if data == "free_contact_username":
        username = getattr(user, "username", None)
        if not username:
            await query.answer()
            await query.message.reply_text(
                "У вас не установлен username в Telegram. Пожалуйста, оставьте номер телефона."
            )
            return
        if OWNER_CHAT_ID:
            lines = [
                "📬 Контакт из режима свободного вопроса (username)",
                f"User ID: {user.id if user else '–'}",
                f"Username: @{username}",
                f"Имя: {user.full_name}" if getattr(user, "full_name", None) else "",
            ]
            msg_text = "\n".join([ln for ln in lines if ln])
            await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=msg_text)
        await query.message.reply_text(
            "Спасибо! Я сохранил ваш @username как контакт.",
            reply_markup=main_menu_keyboard(lang, free_mode=True),
        )
        return


async def free_contact_phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user and update.effective_user.id == OWNER_CHAT_ID:
        return
    contact = update.message.contact
    user = update.effective_user
    lang = get_lang(update)
    if not contact:
        return
    if OWNER_CHAT_ID:
        lines = [
            "📬 Контакт из режима свободного вопроса (телефон)",
            f"User ID: {user.id if user else '–'}",
            f"Username: @{user.username}" if getattr(user, "username", None) else "Username: –",
            f"Имя: {user.full_name}" if getattr(user, "full_name", None) else "",
            f"Телефон: {contact.phone_number}",
        ]
        msg_text = "\n".join([ln for ln in lines if ln])
        await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=msg_text)
    await update.message.reply_text(
        "Спасибо! Я сохранил ваш номер телефона.",
        reply_markup=main_menu_keyboard(lang, free_mode=True),
    )


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    if update.effective_user and update.effective_user.id == OWNER_CHAT_ID:
        return
    text = (update.message.text or "").strip()
    if text == t("btn_plan", lang):
        return await plan_start(update, context)
    if text == t("btn_doctor", lang):
        return await doctor_menu_start(update, context)
    if text == t("btn_contact", lang):
        return await contact_start(update, context)
    if text == t("btn_faq", lang):
        return await faq_menu_entry(update, context)
    if text == t("btn_free_question", lang):
        return await explain_free_question(update, context)
    if text == t("btn_end_free", lang):
        context.user_data["free_mode"] = False
        await update.message.reply_text(
            "Диалог завершён. Возвращаю вас в главное меню.",
            reply_markup=main_menu_keyboard(lang),
        )
        return
    if context.user_data.get("free_mode"):
        return await forward_free_message(update, context)
    await update.message.reply_text(
        t("unknown_command", lang),
        reply_markup=main_menu_keyboard(lang),
    )


PLAN_MENU = "plan_menu"
PLAN_BACK_MAIN = "plan_back_main"
PLAN_WHAT = "plan_what"
PLAN_RISK = "plan_risk"
PLAN_BENEFIT = "plan_benefit"
PLAN_IF_FOUND = "plan_if_found"
PLAN_HOW = "plan_how"


def build_plan_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Что вообще проверяют?", callback_data=PLAN_WHAT)],
        [InlineKeyboardButton("Какой риск может быть?", callback_data=PLAN_RISK)],
        [InlineKeyboardButton("Чем это полезно паре?", callback_data=PLAN_BENEFIT)],
        [InlineKeyboardButton("Что если найдут риск?", callback_data=PLAN_IF_FOUND)],
        [InlineKeyboardButton("Как проходит анализ?", callback_data=PLAN_HOW)],
        [InlineKeyboardButton("Подобрать подходящий тест", callback_data="contact_from_plan")],
        [InlineKeyboardButton("🔙 В главное меню", callback_data=PLAN_BACK_MAIN)],
    ]
    return InlineKeyboardMarkup(keyboard)


async def plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = build_plan_main_keyboard()
    await update.message.reply_text(
        "👶 *Планируем / ждём ребёнка*\n\nВыберите, что именно вам интересно:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data == PLAN_BACK_MAIN:
        await query.edit_message_text("Возвращаю в главное меню…")
        return await show_main_menu(update, context)
    text = ""
    keyboard = None
    if data == PLAN_WHAT:
        text = (
            "🔬 *Что вообще проверяют?*\n\n"
            "Скрининг на носительство — это анализ ДНК, который смотрит, "
            "несёт ли человек изменения в генах, связанные с тяжёлыми наследственными заболеваниями.\n\n"
            "Важно: у самого носителя заболевание обычно не проявляется. "
            "Риск появляется, когда два носителя одного и того же заболевания планируют ребёнка."
        )
        keyboard = build_plan_main_keyboard()
    elif data == PLAN_RISK:
        text = (
            "📊 *Какой риск может быть?*\n\n"
            "Если оба родителя являются носителями одного и того же заболевания, "
            "то в каждой беременности:\n"
            "• 25% — ребёнок с заболеванием;\n"
            "• 50% — ребёнок здоров, но носитель;\n"
            "• 25% — ребёнок без мутации.\n\n"
            "Скрининг помогает узнать об этом риске заранее."
        )
        keyboard = build_plan_main_keyboard()
    elif data == PLAN_BENEFIT:
        text = (
            "💡 *Чем это полезно паре?*\n\n"
            "Если риск обнаружен заранее, у пары есть несколько вариантов:\n"
            "• планировать беременность с учётом риска;\n"
            "• использовать ЭКО с преимплантационной генетической диагностикой (ПГТ);\n"
            "• рассмотреть донорские клетки;\n"
            "• принять осознанное решение идти своим путём, но уже зная о рисках.\n\n"
            "Главная идея — больше осознанности и меньше неожиданностей."
        )
        keyboard = build_plan_main_keyboard()
    elif data == PLAN_IF_FOUND:
        text = (
            "❗ *Что если найдут риск?*\n\n"
            "1. Врач-генетик объяснит, о каком заболевании идёт речь и как оно проявляется.\n"
            "2. Обсудит с вами возможные варианты действий.\n"
            "3. Поможет спланировать дальнейшие шаги (включая варианты ЭКО + ПГТ, "
            "донорские клетки и др.).\n\n"
            "Наличие риска — это не приговор, а информация для выбора."
        )
        keyboard = build_plan_main_keyboard()
    elif data == PLAN_HOW:
        text = (
            "🧪 *Как проходит анализ?*\n\n"
            "Обычно это забор крови из вены или мазок из щеки. Дальше лаборатория "
            "анализирует ДНК, и через некоторое время вы получаете понятный отчёт.\n\n"
            "Время выполнения и формат отчёта зависят от конкретного теста."
        )
        keyboard = build_plan_main_keyboard()
    if text and keyboard:
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")


CONTACT_NAME, CONTACT_PHONE, CONTACT_HOW, CONTACT_COMMENT = range(4)


def build_contact_method_keyboard(lang: str, user) -> ReplyKeyboardMarkup:
    rows = [["📞 Оставить номер телефона"]]
    username = getattr(user, "username", None) if user else None
    if username:
        rows.append(["@ Использовать мой @username"])
    rows.append(["✉️ Другая форма связи (email или т.п.)"])
    rows.append([t("btn_back", lang), t("btn_cancel", lang)])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


async def contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    context.user_data["contact"] = {}
    await update.message.reply_text(
        t("name_ask", lang),
        reply_markup=ReplyKeyboardMarkup(
            [[t("btn_cancel", lang)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    return CONTACT_NAME


async def contact_start_from_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    context.user_data["contact"] = {"source": "plan"}
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        t("name_ask", lang),
        reply_markup=ReplyKeyboardMarkup(
            [[t("btn_cancel", lang)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    return CONTACT_NAME


async def contact_start_from_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    context.user_data["contact"] = {"source": "doctor"}
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        t("name_ask", lang),
        reply_markup=ReplyKeyboardMarkup(
            [[t("btn_cancel", lang)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    return CONTACT_NAME


async def contact_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = (update.message.text or "").strip()
    if is_cancel(text, lang):
        await update.message.reply_text(
            "Отменено. Возвращаю вас в главное меню.",
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END
    context.user_data["contact"]["name"] = text
    kb = build_contact_method_keyboard(lang, update.effective_user)
    await update.message.reply_text(
        "Как с вами связаться?",
        reply_markup=kb,
    )
    return CONTACT_HOW


async def contact_how(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = (update.message.text or "").strip()
    if is_cancel(text, lang):
        await update.message.reply_text(
            "Отменено. Возвращаю вас в главное меню.",
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END
    if is_back(text, lang):
        await update.message.reply_text(
            t("name_ask", lang),
            reply_markup=ReplyKeyboardMarkup(
                [[t("btn_cancel", lang)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return CONTACT_NAME
    if text == "📞 Оставить номер телефона":
        context.user_data["contact"]["how"] = "Телефон"
        kb = ReplyKeyboardMarkup(
            [
                [KeyboardButton("📱 Отправить номер телефона", request_contact=True)],
                [t("btn_back", lang), t("btn_cancel", lang)],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(
            "Нажмите кнопку ниже, чтобы отправить номер телефона:",
            reply_markup=kb,
        )
        return CONTACT_PHONE
    if text == "@ Использовать мой @username":
        user = update.effective_user
        username = getattr(user, "username", None) if user else None
        if not username:
            kb = build_contact_method_keyboard(lang, user)
            await update.message.reply_text(
                "У вас не установлен username в Telegram. Пожалуйста, выберите другой способ связи.",
                reply_markup=kb,
            )
            return CONTACT_HOW
        context.user_data["contact"]["how"] = "Telegram username"
        context.user_data["contact"]["phone"] = f"@{username}"
        await update.message.reply_text(
            t("comment_ask", lang),
            reply_markup=ReplyKeyboardMarkup(
                [[t("btn_back", lang), t("btn_cancel", lang)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return CONTACT_COMMENT
    if text.startswith("✉️"):
        context.user_data["contact"]["how"] = "Другая форма связи"
        await update.message.reply_text(
            "Напишите удобный способ связи (email или другой мессенджер):",
            reply_markup=ReplyKeyboardMarkup(
                [[t("btn_back", lang), t("btn_cancel", lang)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return CONTACT_PHONE
    await update.message.reply_text(
        "Пожалуйста, выберите один из предложенных вариантов.",
        reply_markup=build_contact_method_keyboard(lang, update.effective_user),
    )
    return CONTACT_HOW


async def contact_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    data = context.user_data.get("contact", {})
    how = data.get("how")
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        context.user_data["contact"]["phone"] = phone_number
        if not how:
            context.user_data["contact"]["how"] = "Телефон"
        await update.message.reply_text(
            t("comment_ask", lang),
            reply_markup=ReplyKeyboardMarkup(
                [[t("btn_back", lang), t("btn_cancel", lang)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return CONTACT_COMMENT
    text = (update.message.text or "").strip()
    if is_cancel(text, lang):
        await update.message.reply_text(
            "Отменено. Возвращаю вас в главное меню.",
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END
    if is_back(text, lang):
        kb = build_contact_method_keyboard(lang, update.effective_user)
        await update.message.reply_text(
            "Как с вами связаться?",
            reply_markup=kb,
        )
        return CONTACT_HOW
    if how == "Другая форма связи":
        context.user_data["contact"]["phone"] = text
        await update.message.reply_text(
            t("comment_ask", lang),
            reply_markup=ReplyKeyboardMarkup(
                [[t("btn_back", lang), t("btn_cancel", lang)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return CONTACT_COMMENT
    if not is_valid_phone(text):
        await update.message.reply_text(
            t("phone_invalid", lang),
            reply_markup=ReplyKeyboardMarkup(
                [[t("btn_back", lang), t("btn_cancel", lang)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return CONTACT_PHONE
    context.user_data["contact"]["phone"] = text
    if not how:
        context.user_data["contact"]["how"] = "Телефон"
    await update.message.reply_text(
        t("comment_ask", lang),
        reply_markup=ReplyKeyboardMarkup(
            [[t("btn_back", lang), t("btn_cancel", lang)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    return CONTACT_COMMENT


async def contact_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = (update.message.text or "").strip()
    if is_cancel(text, lang):
        await update.message.reply_text(
            "Отменено. Возвращаю вас в главное меню.",
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END
    if is_back(text, lang):
        kb = build_contact_method_keyboard(lang, update.effective_user)
        await update.message.reply_text(
            "Как с вами связаться?",
            reply_markup=kb,
        )
        return CONTACT_HOW
    context.user_data["contact"]["comment"] = text
    data = context.user_data.get("contact", {})
    name = data.get("name", "-")
    phone = data.get("phone", "-")
    how = data.get("how", "-")
    comment = data.get("comment", "-")
    source = data.get("source", "-")
    user = update.effective_user
    user_id = user.id if user else "–"
    username = getattr(user, "username", None)
    full_name = getattr(user, "full_name", None)
    owner_lines = [
        t("lead_sent_owner_title", lang),
        "",
        f"User ID: {user_id}",
        f"Username: @{username}" if username else "Username: –",
        f"Имя в Telegram: {full_name}" if full_name else "",
        "",
        f"Имя (из заявки): {name}",
        f"Телефон: {phone}",
        f"Как связаться удобнее: {how}",
        f"Комментарий: {comment}",
        f"Источник: {source}",
    ]
    owner_text = "\n".join([ln for ln in owner_lines if ln])
    if OWNER_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=owner_text)
        except Exception as e:
            logger.error(f"Failed to send lead to owner: {e}")
    await update.message.reply_text(
        t("contact_done_user", lang),
        reply_markup=main_menu_keyboard(lang),
    )
    return ConversationHandler.END


PatientFaqItem = Dict[str, Any]


PATIENT_FAQ_LIST: List[PatientFaqItem] = [
    {
        "id": "what_is_screening",
        "title": "Что такое скрининг на носительство наследственных заболеваний?",
        "answer": (
            "Скрининг на носительство — это анализ ДНК, который показывает, "
            "является ли человек носителем генетических изменений, "
            "связанных с тяжёлыми наследственными заболеваниями.\n\n"
            "Важно: у самого носителя заболевание, как правило, не проявляется. "
            "Риск возникает, если оба будущих родителя являются носителями одного и того же заболевания."
        ),
    },
    {
        "id": "who_needs",
        "title": "Кому имеет смысл проходить такой скрининг?",
        "answer": (
            "Чаще всего скрининг на носительство рекомендуют парам, которые планируют беременность "
            "или уже ждут ребёнка.\n\n"
            "Особенно полезен анализ, если:\n"
            "• в семье были случаи тяжёлых наследственных заболеваний;\n"
            "• супруги состоят в родстве;\n"
            "• пара хочет заранее оценить возможные генетические риски.\n\n"
            "Но пройти скрининг может и любой взрослый человек, который задумывается о здоровье будущих детей."
        ),
    },
    {
        "id": "difference_from_other_tests",
        "title": "Чем скрининг на носительство отличается от других генетических тестов?",
        "answer": (
            "Скрининг на носительство фокусируется именно на выявлении носительства "
            "ряда конкретных наследственных заболеваний. Он не ставит диагноз, "
            "а оценивает риск.\n\n"
            "Он отличается от, например, тестов по фармакогенетике, онкогенетике "
            "или \"генетических паспортов\", у которых другая цель и другой набор генов."
        ),
    },
    {
        "id": "what_if_both_carriers",
        "title": "Что будет, если у обоих супругов найдут совпадающее носительство?",
        "answer": (
            "Если у обоих будущих родителей выявлено носительство одного и того же заболевания, "
            "то в каждой беременности есть риск рождения ребёнка с этим заболеванием.\n\n"
            "Обычно говорят о вероятностях:\n"
            "• 25% — ребёнок с заболеванием;\n"
            "• 50% — ребёнок здоров, но тоже носитель;\n"
            "• 25% — ребёнок без выявленной мутации.\n\n"
            "При этом у пары появляется возможность заранее обсудить варианты с врачом-генетиком: "
            "от ЭКО с преимплантационной диагностикой до других решений."
        ),
    },
    {
        "id": "when_to_do",
        "title": "Когда лучше проходить скрининг на носительство?",
        "answer": (
            "Оптимальное время — ещё до зачатия. Так у пары есть максимальный выбор вариантов.\n\n"
            "Но пройти скрининг можно и во время беременности — это тоже даёт полезную информацию "
            "и помогает планировать дальнейшие шаги вместе с врачами."
        ),
    },
]


def build_patient_faq_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(item["title"], callback_data=f"faq_{item['id']}")]
        for item in PATIENT_FAQ_LIST
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Назад в главное меню", callback_data="faq_back")])
    return InlineKeyboardMarkup(keyboard)


async def faq_menu_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = t("faq_menu_title", lang)
    kb = build_patient_faq_keyboard()
    if update.message:
        await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")


async def faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data == "faq_back":
        await query.edit_message_text("Возвращаю в главное меню…")
        return await show_main_menu(update, context)
    faq_id = data.replace("faq_", "", 1)
    item = next((x for x in PATIENT_FAQ_LIST if x["id"] == faq_id), None)
    if not item:
        await query.edit_message_text(
            "Выберите вопрос из меню ниже.",
            reply_markup=build_patient_faq_keyboard(),
        )
        return
    await query.edit_message_text(
        item["answer"],
        reply_markup=build_patient_faq_keyboard(),
        parse_mode="Markdown",
    )


DOCTOR_MENU_SCREENING = "doctor_menu_screening"
DOCTOR_MENU_HOW_TO_RECOMMEND = "doctor_menu_how_to_recommend"
DOCTOR_MENU_WHICH_TEST = "doctor_menu_which_test"
DOCTOR_MENU_PATIENT_TYPES = "doctor_menu_patient_types"
DOCTOR_MENU_CONTACT = "doctor_menu_contact"
DOCTOR_MENU_FAQ = "doctor_menu_faq"


def build_doctor_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Что такое скрининг на носительство для практикующего врача?", callback_data=DOCTOR_MENU_SCREENING)],
        [InlineKeyboardButton("Как объяснить пациенту, зачем это нужно?", callback_data=DOCTOR_MENU_HOW_TO_RECOMMEND)],
        [InlineKeyboardButton("Какой тест выбрать в практике?", callback_data=DOCTOR_MENU_WHICH_TEST)],
        [InlineKeyboardButton("Каким пациентам особенно важно предложить тест?", callback_data=DOCTOR_MENU_PATIENT_TYPES)],
        [InlineKeyboardButton("Оставить заявку на сотрудничество", callback_data=DOCTOR_MENU_CONTACT)],
        [InlineKeyboardButton("FAQ для врачей", callback_data=DOCTOR_MENU_FAQ)],
        [InlineKeyboardButton("🔙 В главное меню", callback_data="doc_back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def doctor_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = build_doctor_main_keyboard()
    await update.message.reply_text(
        "👨‍⚕️ *Я врач*\n\nВыберите, что вам интересно:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def doctor_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data == "doc_back_main":
        await query.edit_message_text("Возвращаю в главное меню…")
        return await show_main_menu(update, context)
    text = ""
    keyboard = None
    if data == DOCTOR_MENU_SCREENING:
        text = (
            "👨‍⚕️ *Скрининг на носительство для практикующего врача*\n\n"
            "Это инструмент, который позволяет заранее выявить пары с повышенным риском "
            "рождения ребёнка с наследственным заболеванием.\n\n"
            "Для врача это дополнительный ресурс:\n"
            "• для осознанного планирования беременности вместе с пациентами;\n"
            "• для снижения числа неожиданных тяжёлых случаев;\n"
            "• для повышения качества консультирования."
        )
        keyboard = build_doctor_main_keyboard()
    elif data == DOCTOR_MENU_HOW_TO_RECOMMEND:
        text = (
            "🗣 *Как объяснить пациенту, зачем это нужно?*\n\n"
            "Часто пациенты никогда не слышали о скрининге на носительство. "
            "Работают простые формулировки:\n\n"
            "• «Это анализ, который помогает заранее узнать риски наследственных заболеваний у детей»;\n"
            "• «Он не ставит диагноз, а отвечает на вопрос: “Есть ли у пары скрытый риск?”»;\n"
            "• «Если риск есть, у нас появляется больше вариантов, что делать дальше».\n\n"
            "Важно говорить простым языком, без избыточной терминологии."
        )
        keyboard = build_doctor_main_keyboard()
    elif data == DOCTOR_MENU_WHICH_TEST:
        text = (
            "🧾 *Какой тест выбрать в практике?*\n\n"
            "Вариантов тестов много: от таргетных панелей до расширенных исследований.\n\n"
            "Часто имеет смысл исходить из:\n"
            "• национальных/этнических особенностей пары;\n"
            "• семейного анамнеза;\n"
            "• выбранной тактики планирования беременности.\n\n"
            "Оптимально — обсудить с лабораторией несколько рабочих сценариев, "
            "чтобы врач заранее понимал, в каких случаях какой тест рекомендовать."
        )
        keyboard = build_doctor_main_keyboard()
    elif data == DOCTOR_MENU_PATIENT_TYPES:
        text = (
            "👥 *Каким пациентам особенно важно предложить тест?*\n\n"
            "В практике часто выделяют группы:\n"
            "• пары с отягощённым семейным анамнезом по наследственным заболеваниям;\n"
            "• супружеские пары, состоящие в родстве;\n"
            "• пациенты из популяций с известной высокой частотой отдельных заболеваний;\n"
            "• пары, уже столкнувшиеся с неблагоприятным исходом беременности.\n\n"
            "Но предлагать скрининг можно и более широкой группе — как часть подготовки к беременности."
        )
        keyboard = build_doctor_main_keyboard()
    elif data == DOCTOR_MENU_CONTACT:
        text = (
            "📨 *Оставить заявку на сотрудничество*\n\n"
            "Если вы хотите:\n"
            "• получать понятные материалы для пациентов;\n"
            "• подобрать оптимальные тесты под вашу практику;\n"
            "• обсудить индивидуальные схемы взаимодействия с лабораторией,\n\n"
            "— вы можете оставить свои контакты через раздел «Записаться / Оставить контакты» в главном меню.\n\n"
            "Мы свяжемся с вами и обсудим детали."
        )
        keyboard = build_doctor_main_keyboard()
    elif data == DOCTOR_MENU_FAQ:
        return await doctor_faq_menu_entry(update, context)
    if text and keyboard:
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")


DoctorFaqItem = Dict[str, Any]


DOCTOR_FAQ_LIST: List[DoctorFaqItem] = [
    {
        "id": "how_to_start",
        "title": "С чего начать внедрение скрининга на носительство в практике?",
        "answer": (
            "1. Определите, в каких группах пациентов скрининг будет наиболее полезен.\n"
            "2. Обсудите с лабораторией доступные панели и форматы.\n"
            "3. Подготовьте короткие объяснения для пациентов (1–2 минуты).\n"
            "4. Включите обсуждение генетических рисков в стандартные приёмы до беременности."
        ),
    },
    {
        "id": "how_to_explain_risk",
        "title": "Как простыми словами объяснить риск пациенту?",
        "answer": (
            "Используйте аналогии и простые формулировки. Например:\n"
            "«У большинства людей есть “скрытые” генетические особенности. "
            "Обычно они никак не проявляются. Но если у пары совпадают такие особенности, "
            "может родиться ребёнок с заболеванием. Скрининг помогает заранее узнать, есть ли такой риск»."
        ),
    },
    {
        "id": "what_if_patient_afraid",
        "title": "Что делать, если пациент боится анализа?",
        "answer": (
            "Важно признать его чувства и подчеркнуть, что скрининг — это именно инструмент для выбора, а не приговор.\n\n"
            "Можно сказать:\n"
            "«Этот анализ не говорит, что с вашим ребёнком обязательно что-то случится. "
            "Он помогает заранее понять, есть ли скрытый риск, и если да — мы сможем вместе решить, как с этим быть»."
        ),
    },
    {
        "id": "how_to_discuss_positive_result",
        "title": "Как обсуждать с пациентом высокий риск или совпадение носительства?",
        "answer": (
            "1. Спокойно объяснить, о каком заболевании идёт речь и как оно протекает.\n"
            "2. Обсудить варианты: от дополнительных обследований до ЭКО с ПГТ.\n"
            "3. Подчеркнуть, что у пары есть время и пространство для взвешенного решения.\n"
            "4. При необходимости — направить к профильным специалистам."
        ),
    },
]


def build_doctor_faq_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(item["title"], callback_data=f"dfaq_{item['id']}")]
        for item in DOCTOR_FAQ_LIST
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Назад в главное меню", callback_data="dfaq_back")])
    return InlineKeyboardMarkup(keyboard)


async def doctor_faq_menu_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = t("faq_doctor_title", lang) + t("doctor_intro", lang)
    kb = build_doctor_faq_keyboard()
    if update.message:
        await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        q = update.callback_query
        await q.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")


async def doctor_faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data == "dfaq_back":
        await query.edit_message_text("Возвращаю в главное меню…")
        return await show_main_menu(update, context)
    faq_id = data.replace("dfaq_", "", 1)
    item = next((x for x in DOCTOR_FAQ_LIST if x["id"] == faq_id), None)
    if not item:
        await query.edit_message_text(
            "Выберите вопрос из меню ниже.",
            reply_markup=build_doctor_faq_keyboard(),
        )
        return
    await query.edit_message_text(
        item["answer"],
        reply_markup=build_doctor_faq_keyboard(),
        parse_mode="Markdown",
    )


async def owner_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.id != OWNER_CHAT_ID:
        return
    msg = update.message
    if not msg or not msg.text:
        return
    if not msg.reply_to_message or not msg.reply_to_message.text:
        return
    original_text = msg.reply_to_message.text
    match = re.search(r"User ID:\s*(\d+)", original_text)
    if not match:
        return
    user_id = int(match.group(1))
    try:
        await context.bot.send_message(chat_id=user_id, text=msg.text)
    except Exception as e:
        logger.error("Failed to forward owner reply to %s: %s", user_id, e)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN!")
    app = Application.builder().token(BOT_TOKEN).build()
    from re import escape
    pattern = rf"^{escape(t('btn_contact', 'ru'))}$|^{escape(t('btn_contact', 'en'))}$"
    contact_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(pattern), contact_start),
            CallbackQueryHandler(contact_start_from_plan, pattern=r"^contact_from_plan$"),
            CallbackQueryHandler(contact_start_from_doctor, pattern=r"^contact_from_doctor$"),
        ],
        states={
            CONTACT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_name)],
            CONTACT_PHONE: [MessageHandler(((filters.TEXT & ~filters.COMMAND) | filters.CONTACT), contact_phone)],
            CONTACT_HOW: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_how)],
            CONTACT_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_comment)],
        },
        fallbacks=[
            MessageHandler(filters.Regex(r"^❌ Отмена$|^❌ Cancel$"), contact_comment),
        ],
        allow_reentry=True,
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(contact_conv)
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Chat(OWNER_CHAT_ID),
            owner_auto_reply,
        )
    )
    app.add_handler(
        MessageHandler(
            filters.CONTACT & ~filters.Chat(OWNER_CHAT_ID),
            free_contact_phone_handler,
        )
    )
    app.add_handler(CallbackQueryHandler(free_contact_callback, pattern=r"^free_contact_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))
    app.add_handler(CallbackQueryHandler(plan_callback, pattern=r"^plan_"))
    app.add_handler(CallbackQueryHandler(doctor_menu_callback, pattern=r"^(doctor_menu_|doc_back_)"))
    app.add_handler(CallbackQueryHandler(faq_answer, pattern=r"^faq_"))
    app.add_handler(CallbackQueryHandler(doctor_faq_answer, pattern=r"^dfaq_"))
    app.run_polling()


if __name__ == "__main__":
    main()
