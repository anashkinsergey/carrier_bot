import os
import re
import logging
from typing import Dict, Any, List, Optional

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
logger.info("Bot started: carrier_screening_bot")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "0"))

# Чтобы deeplink всегда был корректным:
# BOT_USERNAME=CarrierScreeningBot
BOT_USERNAME = os.environ.get("BOT_USERNAME", "CarrierScreeningBot").lstrip("@").strip()


def deeplink(payload: str) -> str:
    # payload: question / plan / doctor
    return f"https://t.me/{BOT_USERNAME}?start={payload}"


def t(label: str, lang: str = "ru") -> str:
    texts = {
        "greeting": {
            "ru": (
                "Здесь можно спокойно разобраться, есть ли в вашей ситуации вопрос по генетике.\n\n"
                "Любой вопрос здесь уместен — даже если он кажется простым или «глупым».\n\n"
                "Можно задать свой вопрос — коротко или как получится.\n"
                "Можно просто посмотреть варианты.\n"
                "Можно закрыть тему и вернуться позже.\n\n"
                "Если не знаете, с чего начать — напишите 2–3 предложения о вашей ситуации как получится.\n\n"
                "Важно: это не консультация и не запись к врачу."
            ),
            "en": (
                "Here you can calmly understand whether genetics is relevant to your situation.\n\n"
                "Any question is welcome — even if it seems simple.\n\n"
                "You can ask your question — short or however it comes out.\n"
                "You can just browse options.\n"
                "You can close the topic and return later.\n\n"
                "If you don’t know where to start — write 2–3 sentences about your situation.\n\n"
                "Important: this is not a medical consultation and not an appointment booking."
            ),
        },
        "main_menu_title": {"ru": "Выберите раздел:", "en": "Choose a section:"},

        # Кнопки главного меню
        "btn_plan": {"ru": "👶 Планируем / ждём ребёнка", "en": "👶 Planning / expecting a baby"},
        "btn_doctor": {"ru": "👨‍⚕️ Я врач", "en": "👨‍⚕️ I am a doctor"},
        "btn_contact": {"ru": "📱 Оставить контакты", "en": "📱 Leave contacts"},
        "btn_free_question": {"ru": "✍️ Написать свой вопрос", "en": "✍️ Write my question"},
        "btn_end_free": {"ru": "Закончить диалог / Вернуться к меню", "en": "End dialog / Back to menu"},
        "btn_faq": {"ru": "❓ FAQ", "en": "❓ FAQ"},

        # Подсказки режима "свободного вопроса"
        "free_q_button_explain": {
            "ru": (
                "Напишите здесь свой вопрос (одним или несколькими сообщениями) — как получается.\n\n"
                "Контакты оставлять не обязательно.\n"
                "Если захотите — сможете оставить телефон или @username после отправки вопроса."
            ),
            "en": (
                "Type your question here (one or several messages) — however it comes out.\n\n"
                "Leaving contacts is optional.\n"
                "If you want, you can leave a phone or @username after sending the question."
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
        "free_q_owner_title": {"ru": "Новое сообщение в боте (без заявки)", "en": "New bot message (no lead form)"},
        "unknown_command": {
            "ru": "Пока не знаю, что делать с этим. Используйте меню ниже.",
            "en": "I don’t know what to do with that. Use the menu below.",
        },

        # Контакты / форма
        "btn_back": {"ru": "⬅️ Назад", "en": "⬅️ Back"},
        "btn_cancel": {"ru": "❌ Отмена", "en": "❌ Cancel"},
        "name_ask": {"ru": "Как к вам обращаться? (имя или имя + фамилия)", "en": "How should I call you? (name or full name)"},
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
        "lead_sent_owner_title": {"ru": "Новая заявка", "en": "New Lead"},

        # FAQ меню
        "faq_menu_title": {
            "ru": "❓ *FAQ по скринингу на носительство*\n\nВыберите вопрос:",
            "en": "❓ *Carrier screening FAQ*\n\nChoose a question:",
        },
        "faq_doctor_title": {"ru": "👨‍⚕️ *FAQ для врачей*\n", "en": "👨‍⚕️ *Doctor FAQ*\n"},
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
    return ReplyKeyboardMarkup([[t("btn_back", lang), t("btn_cancel", lang)]], resize_keyboard=True)


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


def looks_like_question(text: str) -> bool:
    """
    Мягкая эвристика: если человек пишет "живой текст", считаем это вопросом.
    Не пытаемся быть умнее человека: лучше принять и переслать, чем потерять.
    """
    ttxt = (text or "").strip()
    if not ttxt:
        return False
    if len(ttxt) >= 25:
        return True
    if "?" in ttxt:
        return True
    # короткие "наводки"
    triggers = [
        "подскаж",
        "нужно ли",
        "стоит ли",
        "как быть",
        "что делать",
        "мы планируем",
        "беременность",
        "скрининг",
        "носительство",
        "генетик",
        "анализ",
        "тест",
    ]
    low = ttxt.lower()
    return any(x in low for x in triggers)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)

    # Deeplink payload: /start <payload>
    payload: Optional[str] = None
    if context.args:
        payload = (context.args[0] or "").strip().lower()

    # По payload можно сразу увести в нужный сценарий
    if payload == "question":
        # сразу включаем режим вопроса
        context.user_data["free_mode"] = True
        await update.message.reply_text(
            t("free_q_button_explain", lang),
            reply_markup=main_menu_keyboard(lang, free_mode=True),
        )
        return
    if payload == "plan":
        await update.message.reply_text(t("greeting", lang), reply_markup=main_menu_keyboard(lang))
        return await plan_start(update, context)
    if payload == "doctor":
        await update.message.reply_text(t("greeting", lang), reply_markup=main_menu_keyboard(lang))
        return await doctor_menu_start(update, context)

    # обычный /start
    await update.message.reply_text(t("greeting", lang), reply_markup=main_menu_keyboard(lang))


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
    """
    Пересылаем любое сообщение пользователя владельцу.
    """
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
            [InlineKeyboardButton("Оставить номер телефона", callback_data="free_contact_phone")],
            [InlineKeyboardButton("Использовать мой @username", callback_data="free_contact_username")],
        ]
    )
    await update.message.reply_text(
        "Если захотите, можно оставить контакт (не обязательно):",
        reply_markup=contact_keyboard,
    )


async def free_contact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user
    lang = get_lang(update)

    if data == "free_contact_phone":
        kb = ReplyKeyboardMarkup(
            [[KeyboardButton("Отправить номер телефона", request_contact=True)]],
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
            await query.message.reply_text("У вас не установлен username в Telegram. Можно оставить номер телефона.")
            return

        if OWNER_CHAT_ID:
            lines = [
                "Контакт из режима свободного вопроса (username)",
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
            "Контакт из режима свободного вопроса (телефон)",
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

    # Совместимость со старой кнопкой (вдруг у кого-то сохранилось)
    legacy_free_question = ["/Написать свой вопрос", "/Write my question"]

    if text == t("btn_plan", lang):
        return await plan_start(update, context)

    if text == t("btn_doctor", lang):
        return await doctor_menu_start(update, context)

    if text == t("btn_contact", lang):
        return await contact_start(update, context)

    if text == t("btn_faq", lang):
        return await faq_menu_entry(update, context)

    if text == t("btn_free_question", lang) or text in legacy_free_question:
        return await explain_free_question(update, context)

    if text == t("btn_end_free", lang):
        context.user_data["free_mode"] = False
        await update.message.reply_text(
            "Диалог завершён. Возвращаю вас в главное меню.",
            reply_markup=main_menu_keyboard(lang),
        )
        return

    # Если мы уже в режиме свободного вопроса — всё пересылаем
    if context.user_data.get("free_mode"):
        return await forward_free_message(update, context)

    # Если НЕ в free_mode, но текст выглядит как вопрос — тоже считаем это вопросом
    if looks_like_question(text):
        context.user_data["free_mode"] = True
        await update.message.reply_text(
            "Похоже, вы хотите задать вопрос.\n\nНапишите его одним или несколькими сообщениями — как получается.",
            reply_markup=main_menu_keyboard(lang, free_mode=True),
        )
        return await forward_free_message(update, context)

    await update.message.reply_text(t("unknown_command", lang), reply_markup=main_menu_keyboard(lang))


# -------------------------
# Планируем / ждём ребёнка
# -------------------------

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
        [InlineKeyboardButton("Оставить контакты", callback_data="contact_from_plan")],
        [InlineKeyboardButton("В главное меню", callback_data=PLAN_BACK_MAIN)],
    ]
    return InlineKeyboardMarkup(keyboard)


async def plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = build_plan_main_keyboard()
    await update.message.reply_text(
        "Планируем / ждём ребёнка\n\nВыберите, что именно вам интересно:",
        reply_markup=keyboard,
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
            "Что вообще проверяют?\n\n"
            "Скрининг на носительство — это анализ ДНК, который смотрит, "
            "есть ли у человека изменения в генах, связанные с тяжёлыми наследственными заболеваниями.\n\n"
            "Важно: у самого носителя заболевание обычно не проявляется. "
            "Риск появляется, когда два носителя одного и того же заболевания планируют ребёнка."
        )
        keyboard = build_plan_main_keyboard()

    elif data == PLAN_RISK:
        text = (
            "Какой риск может быть?\n\n"
            "Если оба родителя — носители одного и того же заболевания, то в каждой беременности:\n"
            "• 25% — ребёнок с заболеванием;\n"
            "• 50% — ребёнок здоров, но носитель;\n"
            "• 25% — ребёнок без мутации.\n\n"
            "Скрининг помогает узнать об этом риске заранее."
        )
        keyboard = build_plan_main_keyboard()

    elif data == PLAN_BENEFIT:
        text = (
            "Чем это полезно паре?\n\n"
            "Если риск обнаружен заранее, у пары появляется выбор вариантов. Например:\n"
            "• обсудить планирование беременности с учётом риска;\n"
            "• рассмотреть ЭКО с ПГТ;\n"
            "• рассмотреть донорские клетки;\n"
            "• принять своё решение, но уже понимая риски.\n\n"
            "Главная идея — больше ясности и меньше неожиданностей."
        )
        keyboard = build_plan_main_keyboard()

    elif data == PLAN_IF_FOUND:
        text = (
            "Что если найдут риск?\n\n"
            "Обычно дальше:\n"
            "1) врач-генетик объясняет, о каком заболевании речь;\n"
            "2) обсуждает варианты действий;\n"
            "3) помогает спланировать дальнейшие шаги.\n\n"
            "Наличие риска — не приговор, а информация для выбора."
        )
        keyboard = build_plan_main_keyboard()

    elif data == PLAN_HOW:
        text = (
            "Как проходит анализ?\n\n"
            "Обычно это кровь из вены или мазок из щеки. Дальше лаборатория анализирует ДНК, "
            "и вы получаете отчёт.\n\n"
            "Сроки и формат отчёта зависят от конкретного теста."
        )
        keyboard = build_plan_main_keyboard()

    if text and keyboard:
        await query.edit_message_text(text, reply_markup=keyboard)


# -------------------------
# Контакты (Conversation)
# -------------------------

CONTACT_NAME, CONTACT_PHONE, CONTACT_HOW, CONTACT_COMMENT = range(4)


def build_contact_method_keyboard(lang: str, user) -> ReplyKeyboardMarkup:
    rows = [["Оставить номер телефона"]]
    username = getattr(user, "username", None) if user else None
    if username:
        rows.append(["Использовать мой @username"])
    rows.append(["Другая форма связи (email и т.п.)"])
    rows.append([t("btn_back", lang), t("btn_cancel", lang)])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


async def contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    context.user_data["contact"] = {}
    await update.message.reply_text(
        t("name_ask", lang),
        reply_markup=ReplyKeyboardMarkup([[t("btn_cancel", lang)]], resize_keyboard=True, one_time_keyboard=True),
    )
    return CONTACT_NAME


async def contact_start_from_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    context.user_data["contact"] = {"source": "plan"}
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        t("name_ask", lang),
        reply_markup=ReplyKeyboardMarkup([[t("btn_cancel", lang)]], resize_keyboard=True, one_time_keyboard=True),
    )
    return CONTACT_NAME


async def contact_start_from_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    context.user_data["contact"] = {"source": "doctor"}
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        t("name_ask", lang),
        reply_markup=ReplyKeyboardMarkup([[t("btn_cancel", lang)]], resize_keyboard=True, one_time_keyboard=True),
    )
    return CONTACT_NAME


async def contact_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = (update.message.text or "").strip()
    if is_cancel(text, lang):
        await update.message.reply_text("Отменено. Возвращаю вас в главное меню.", reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END

    context.user_data["contact"]["name"] = text
    kb = build_contact_method_keyboard(lang, update.effective_user)
    await update.message.reply_text("Как с вами связаться?", reply_markup=kb)
    return CONTACT_HOW


async def contact_how(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = (update.message.text or "").strip()

    if is_cancel(text, lang):
        await update.message.reply_text("Отменено. Возвращаю вас в главное меню.", reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END

    if is_back(text, lang):
        await update.message.reply_text(
            t("name_ask", lang),
            reply_markup=ReplyKeyboardMarkup([[t("btn_cancel", lang)]], resize_keyboard=True, one_time_keyboard=True),
        )
        return CONTACT_NAME

    if text == "Оставить номер телефона":
        context.user_data["contact"]["how"] = "Телефон"
        kb = ReplyKeyboardMarkup(
            [[KeyboardButton("Отправить номер телефона", request_contact=True)], [t("btn_back", lang), t("btn_cancel", lang)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text("Нажмите кнопку ниже, чтобы отправить номер телефона:", reply_markup=kb)
        return CONTACT_PHONE

    if text == "Использовать мой @username":
        user = update.effective_user
        username = getattr(user, "username", None) if user else None
        if not username:
            await update.message.reply_text("У вас не установлен username в Telegram. Выберите другой способ связи.")
            return CONTACT_HOW

        context.user_data["contact"]["how"] = "Telegram username"
        context.user_data["contact"]["phone"] = f"@{username}"
        await update.message.reply_text(
            t("comment_ask", lang),
            reply_markup=ReplyKeyboardMarkup([[t("btn_back", lang), t("btn_cancel", lang)]], resize_keyboard=True, one_time_keyboard=True),
        )
        return CONTACT_COMMENT

    if text.startswith("Другая форма связи"):
        context.user_data["contact"]["how"] = "Другая форма связи"
        await update.message.reply_text(
            "Напишите удобный способ связи (email или другой мессенджер):",
            reply_markup=ReplyKeyboardMarkup([[t("btn_back", lang), t("btn_cancel", lang)]], resize_keyboard=True, one_time_keyboard=True),
        )
        return CONTACT_PHONE

    await update.message.reply_text("Пожалуйста, выберите один из предложенных вариантов.", reply_markup=build_contact_method_keyboard(lang, update.effective_user))
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
            reply_markup=ReplyKeyboardMarkup([[t("btn_back", lang), t("btn_cancel", lang)]], resize_keyboard=True, one_time_keyboard=True),
        )
        return CONTACT_COMMENT

    text = (update.message.text or "").strip()

    if is_cancel(text, lang):
        await update.message.reply_text("Отменено. Возвращаю вас в главное меню.", reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END

    if is_back(text, lang):
        kb = build_contact_method_keyboard(lang, update.effective_user)
        await update.message.reply_text("Как с вами связаться?", reply_markup=kb)
        return CONTACT_HOW

    if how == "Другая форма связи":
        context.user_data["contact"]["phone"] = text
        await update.message.reply_text(
            t("comment_ask", lang),
            reply_markup=ReplyKeyboardMarkup([[t("btn_back", lang), t("btn_cancel", lang)]], resize_keyboard=True, one_time_keyboard=True),
        )
        return CONTACT_COMMENT

    if not is_valid_phone(text):
        await update.message.reply_text(
            t("phone_invalid", lang),
            reply_markup=ReplyKeyboardMarkup([[t("btn_back", lang), t("btn_cancel", lang)]], resize_keyboard=True, one_time_keyboard=True),
        )
        return CONTACT_PHONE

    context.user_data["contact"]["phone"] = text
    if not how:
        context.user_data["contact"]["how"] = "Телефон"

    await update.message.reply_text(
        t("comment_ask", lang),
        reply_markup=ReplyKeyboardMarkup([[t("btn_back", lang), t("btn_cancel", lang)]], resize_keyboard=True, one_time_keyboard=True),
    )
    return CONTACT_COMMENT


async def contact_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = (update.message.text or "").strip()

    if is_cancel(text, lang):
        await update.message.reply_text("Отменено. Возвращаю вас в главное меню.", reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END

    if is_back(text, lang):
        kb = build_contact_method_keyboard(lang, update.effective_user)
        await update.message.reply_text("Как с вами связаться?", reply_markup=kb)
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
        f"Контакт: {phone}",
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

    await update.message.reply_text(t("contact_done_user", lang), reply_markup=main_menu_keyboard(lang))
    return ConversationHandler.END


# -------------------------
# FAQ (пациенты)
# -------------------------

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
    keyboard = [[InlineKeyboardButton(item["title"], callback_data=f"faq_{item['id']}")] for item in PATIENT_FAQ_LIST]
    keyboard.append([InlineKeyboardButton("В главное меню", callback_data="faq_back")])
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
        await query.edit_message_text("Выберите вопрос из меню ниже.", reply_markup=build_patient_faq_keyboard())
        return

    await query.edit_message_text(item["answer"], reply_markup=build_patient_faq_keyboard())


# -------------------------
# Меню для врачей
# -------------------------

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
        [InlineKeyboardButton("Оставить контакты", callback_data="contact_from_doctor")],
        [InlineKeyboardButton("FAQ для врачей", callback_data=DOCTOR_MENU_FAQ)],
        [InlineKeyboardButton("В главное меню", callback_data="doc_back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def doctor_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = build_doctor_main_keyboard()
    await update.message.reply_text(
        "Я врач\n\nВыберите, что вам интересно:",
        reply_markup=keyboard,
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
            "Скрининг на носительство для практикующего врача\n\n"
            "Инструмент, который помогает заранее выявить пары с повышенным риском "
            "рождения ребёнка с наследственным заболеванием.\n\n"
            "Для врача это может быть полезно:\n"
            "• как часть планирования беременности;\n"
            "• чтобы экономить время на объяснениях;\n"
            "• чтобы снижать число неожиданных тяжёлых случаев."
        )
        keyboard = build_doctor_main_keyboard()

    elif data == DOCTOR_MENU_HOW_TO_RECOMMEND:
        text = (
            "Как объяснить пациенту, зачем это нужно?\n\n"
            "Часто помогают простые формулировки:\n"
            "• «Это анализ, который помогает заранее понять риски наследственных заболеваний у детей»\n"
            "• «Он не ставит диагноз — он отвечает на вопрос: есть ли у пары скрытый риск»\n"
            "• «Если риск есть, появляется выбор вариантов, что делать дальше»"
        )
        keyboard = build_doctor_main_keyboard()

    elif data == DOCTOR_MENU_WHICH_TEST:
        text = (
            "Какой тест выбрать в практике?\n\n"
            "Обычно отталкиваются от:\n"
            "• семейного анамнеза;\n"
            "• этнических особенностей;\n"
            "• тактики планирования беременности.\n\n"
            "Если нужно — можно оставить контакты, чтобы обсудить сценарии под вашу практику."
        )
        keyboard = build_doctor_main_keyboard()

    elif data == DOCTOR_MENU_PATIENT_TYPES:
        text = (
            "Каким пациентам особенно важно предложить тест?\n\n"
            "Часто выделяют группы:\n"
            "• семейный анамнез по наследственным заболеваниям;\n"
            "• близкородственные браки;\n"
            "• неблагоприятные исходы беременности в прошлом;\n"
            "• популяции с высокой частотой отдельных заболеваний.\n\n"
            "Но скрининг может быть и частью обычной подготовки к беременности."
        )
        keyboard = build_doctor_main_keyboard()

    elif data == DOCTOR_MENU_CONTACT:
        text = "Оставить контакты можно в главном меню."
        keyboard = build_doctor_main_keyboard()

    elif data == DOCTOR_MENU_FAQ:
        return await doctor_faq_menu_entry(update, context)

    if text and keyboard:
        await query.edit_message_text(text, reply_markup=keyboard)


DoctorFaqItem = Dict[str, Any]

DOCTOR_FAQ_LIST: List[DoctorFaqItem] = [
    {
        "id": "how_to_start",
        "title": "С чего начать внедрение скрининга на носительство в практике?",
        "answer": (
            "1) Определить, в каких группах пациентов это наиболее уместно.\n"
            "2) Понять, какие панели вы используете как базовые.\n"
            "3) Подготовить 2–3 простые фразы для объяснения пациентам.\n"
            "4) При необходимости — иметь «материал для чтения», чтобы пациент пришёл на повторный разговор подготовленным."
        ),
    },
    {
        "id": "what_if_patient_afraid",
        "title": "Что делать, если пациент боится анализа?",
        "answer": (
            "Обычно помогает спокойная рамка:\n"
            "«Этот анализ не говорит, что обязательно будет проблема. Он помогает понять, есть ли скрытый риск — "
            "и если да, у нас появляется выбор, что делать дальше»."
        ),
    },
]


def build_doctor_faq_keyboard() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(item["title"], callback_data=f"dfaq_{item['id']}")] for item in DOCTOR_FAQ_LIST]
    keyboard.append([InlineKeyboardButton("В главное меню", callback_data="dfaq_back")])
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
        await query.edit_message_text("Выберите вопрос из меню ниже.", reply_markup=build_doctor_faq_keyboard())
        return

    await query.edit_message_text(item["answer"], reply_markup=build_doctor_faq_keyboard())


# -------------------------
# Ответ владельца пользователю (через reply)
# -------------------------

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

    # Контактная форма — вход по кнопке главного меню + по inline из plan/doctor
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
        fallbacks=[MessageHandler(filters.Regex(r"^❌ Отмена$|^❌ Cancel$"), contact_comment)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(contact_conv)

    # Владелец отвечает реплаем на сообщение с User ID -> бот пересылает пользователю
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Chat(OWNER_CHAT_ID),
            owner_auto_reply,
        )
    )

    # Контакт из inline режима вопроса (когда пользователь нажал request_contact)
    app.add_handler(MessageHandler(filters.CONTACT & ~filters.Chat(OWNER_CHAT_ID), free_contact_phone_handler))
    app.add_handler(CallbackQueryHandler(free_contact_callback, pattern=r"^free_contact_"))

    # Главное меню + авто-распознавание вопроса
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))

    # Inline-меню
    app.add_handler(CallbackQueryHandler(plan_callback, pattern=r"^plan_"))
    app.add_handler(CallbackQueryHandler(doctor_menu_callback, pattern=r"^(doctor_menu_|doc_back_)"))
    app.add_handler(CallbackQueryHandler(faq_answer, pattern=r"^faq_"))
    app.add_handler(CallbackQueryHandler(doctor_faq_answer, pattern=r"^dfaq_"))

    app.run_polling()


if __name__ == "__main__":
    main()
