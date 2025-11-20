import os
import re
import logging
from typing import Dict, Any

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logger.info("🚀 Bot started: test commit from VS Code")



BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "0"))

(
    CONTACT_NAME,
    CONTACT_PHONE,
    CONTACT_QUESTION,
    CONTACT_TIME,
    CONTACT_METHOD,
    CONTACT_CONFIRM,
) = range(6)

# ---------- утилиты ----------

def get_lang(update: Update) -> str:
    user = update.effective_user
    code = (user.language_code or "").lower() if user else ""
    if code.startswith("ru"):
        return "ru"
    return "en"


def t(label: str, lang: str = "ru") -> str:
    texts = {
        "greeting": {
            "ru": (
                "Привет! Я бот по скринингу на носительство наследственных заболеваний.\n\n"
                "Чем могу помочь?"
            ),
            "en": (
                "Hi! I'm a bot about carrier screening for inherited diseases.\n\n"
                "How can I help you?"
            ),
        },
        "main_menu_title": {
            "ru": "Выберите раздел:",
            "en": "Choose a section:",
        },
        "btn_plan": {"ru": "👶 Планируем / ждём ребёнка", "en": "👶 Planning / expecting a baby"},
        "btn_doctor": {"ru": "👨‍⚕️ Я врач", "en": "👨‍⚕️ I am a doctor"},
        "btn_contact": {
            "ru": "📝 Записаться / Оставить контакты",
            "en": "📝 Leave contacts / book a call",
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
            "en": "Please send your phone number (with country code, e.g. +7…):",
        },
        "question_ask": {
            "ru": "Кратко опишите, какой у вас вопрос?\n"
                  "(например: планирование беременности, скрининг на носительство, консультация генетика)",
            "en": "Briefly describe your question or situation.",
        },
        "time_ask": {
            "ru": "Когда вам удобно поговорить?\nВыберите вариант или напишите свой:",
            "en": "When is it convenient to talk? Choose an option or type your own:",
        },
        "time_freeform": {
            "ru": "Укажите удобное время для связи в свободной форме:",
            "en": "Please specify a convenient time in free form:",
        },
        "method_ask": {
            "ru": "Как удобнее с вами связаться?",
            "en": "How would you like us to contact you?",
        },
        "contact_canceled": {
            "ru": "Заявка отменена. Если передумаете — просто нажмите снова «Записаться / Оставить контакты».",
            "en": "Request cancelled. If you change your mind, just press “Leave contacts / book a call” again.",
        },
        "contact_summary": {
            "ru": "Проверьте, всё ли верно:\n\n",
            "en": "Please check your data:\n\n",
        },
        "summary_name": {"ru": "Имя", "en": "Name"},
        "summary_phone": {"ru": "Телефон", "en": "Phone"},
        "summary_question": {"ru": "Вопрос", "en": "Question"},
        "summary_time": {"ru": "Удобное время", "en": "Preferred time"},
        "summary_method": {"ru": "Способ связи", "en": "Contact method"},
        "confirm_ask": {
            "ru": "Если всё верно — отправляем заявку?\n\n"
                  "Вы можете отправить, изменить данные или отменить.",
            "en": "If everything is correct, should we send your request?\n\n"
                  "You can send, edit data or cancel.",
        },
        "btn_confirm_send": {"ru": "✅ Всё верно, отправить", "en": "✅ Send"},
        "btn_confirm_edit": {"ru": "✏️ Изменить данные", "en": "✏️ Edit data"},
        "btn_confirm_cancel": {"ru": "❌ Отмена", "en": "❌ Cancel"},
        "lead_sent_user": {
            "ru": "Готово! Я передал вашу заявку. С вами свяжутся в ближайшее время.",
            "en": "Done! Your request has been sent. We will contact you soon.",
        },
        "lead_sent_owner_title": {
            "ru": "📬 НОВАЯ ЗАЯВКА ОТ ПОЛЬЗОВАТЕЛЯ",
            "en": "📬 NEW LEAD FROM USER",
        },
        "unknown_command": {
            "ru": "Я пока не знаю, что с этим сделать. Используйте кнопки меню ниже.",
            "en": "I don’t know what to do with this yet. Please use the menu buttons below.",
        },
        "faq_menu_title": {
            "ru": "❓ *FAQ по скринингу на носительство*\n\nВыберите интересующий вопрос:",
            "en": "❓ *FAQ about carrier screening*\n\nChoose a question:",
        },
        "faq_doctor_title": {
            "ru": "👨‍⚕️ *FAQ для врачей*\n\nВыберите вопрос:",
            "en": "👨‍⚕️ *FAQ for doctors*\n\nChoose a question:",
        },
        "doctor_intro": {
            "ru": (
                "Раздел для врачей. Здесь — рациональное зерно:\n"
                "когда направлять на скрининг, как объяснять пациентам и как использовать результат.\n\n"
                "Выберите вопрос ниже."
            ),
            "en": (
                "Section for doctors: when to refer, how to explain carrier screening "
                "and how to use the results.\n\nChoose a question below."
            ),
        },
    }
    return texts.get(label, {}).get(lang, texts.get(label, {}).get("ru", label))


def main_menu_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t("btn_plan", lang)],
            [t("btn_doctor", lang)],
            [t("btn_contact", lang)],
            [t("btn_faq", lang)],
        ],
        resize_keyboard=True,
    )


def back_cancel_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[t("btn_back", lang), t("btn_cancel", lang)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def is_back(text: str, lang: str) -> bool:
    return text.strip() == t("btn_back", lang)


def is_cancel(text: str, lang: str) -> bool:
    return text.strip() == t("btn_cancel", lang)


# ---------- главное меню ----------

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update)
    msg = update.message or update.callback_query.message  # type: ignore
    await msg.reply_text(
        t("main_menu_title", lang),
        reply_markup=main_menu_keyboard(lang),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update)
    await update.message.reply_text(
        t("greeting", lang),
        reply_markup=main_menu_keyboard(lang),
    )


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update)
    text = (update.message.text or "").strip()

    if text == t("btn_plan", lang):
        msg = (
            "👶 Раздел для пар, которые планируют беременность или ждут ребёнка.\n\n"
            "Скрининг на носительство помогает заранее понять генетические риски "
            "и при необходимости обсудить варианты с врачом-генетиком.\n\n"
            "Если хотите, оставьте контакты — и с вами свяжутся для детального разбора."
        )
        await update.message.reply_text(msg)

    elif text == t("btn_doctor", lang):
        await doctor_faq_menu_entry(update, context)

    elif text == t("btn_contact", lang):
        return await contact_start(update, context)

    elif text == t("btn_faq", lang):
        await faq_menu_entry(update, context)

    else:
        await update.message.reply_text(
            t("unknown_command", lang),
            reply_markup=main_menu_keyboard(lang),
        )


# ---------- контактная форма ----------

async def contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_lang(update)
    context.user_data["lang"] = lang
    context.user_data.setdefault("lead", {})

    kb = ReplyKeyboardMarkup(
        [[t("btn_cancel", lang)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(t("name_ask", lang), reply_markup=kb)
    return CONTACT_NAME


async def contact_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})
    text = (update.message.text or "").strip()

    if is_cancel(text, lang):
        await update.message.reply_text(
            t("contact_canceled", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    lead["name"] = text

    kb = back_cancel_keyboard(lang)
    await update.message.reply_text(t("phone_ask", lang), reply_markup=kb)
    return CONTACT_PHONE


async def contact_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})
    text = (update.message.text or "").strip()

    # Отмена
    if is_cancel(text, lang):
        await update.message.reply_text(
            t("contact_canceled", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    # Назад
    if is_back(text, lang):
        kb = ReplyKeyboardMarkup(
            [[t("btn_cancel", lang)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(t("name_ask", lang), reply_markup=kb)
        return CONTACT_NAME

    # Валидация номера: оставляем только цифры, их должно быть >= 10
    digits = re.findall(r"\d", text)
    if len(digits) < 10:
        if lang == "ru":
            msg = (
                "Похоже, номер в непривычном формате 🤔\n\n"
                "Пожалуйста, отправьте номер телефона *цифрами*, "
                "например: `+7 999 123-45-67`."
            )
        else:
            msg = (
                "This doesn’t look like a valid phone number 🤔\n\n"
                "Please send your phone number *using digits*, "
                "for example: `+1 202 555 0119`."
            )

        kb = back_cancel_keyboard(lang)
        await update.message.reply_text(
            msg,
            reply_markup=kb,
            parse_mode="Markdown",
        )
        return CONTACT_PHONE  # остаёмся на шаге ввода телефона

    # если ок — сохраняем как есть (в исходном формате пользователя)
    lead["phone"] = text

    kb = back_cancel_keyboard(lang)
    await update.message.reply_text(t("question_ask", lang), reply_markup=kb)
    return CONTACT_QUESTION


async def contact_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})
    text = (update.message.text or "").strip()

    if is_cancel(text, lang):
        await update.message.reply_text(
            t("contact_canceled", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if is_back(text, lang):
        kb = back_cancel_keyboard(lang)
        await update.message.reply_text(t("phone_ask", lang), reply_markup=kb)
        return CONTACT_PHONE

    lead["question"] = text

    kb = ReplyKeyboardMarkup(
        [
            ["Утром", "Днём"],
            ["Вечером", "Не принципиально"],
            [t("btn_back", lang), t("btn_cancel", lang)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(t("time_ask", lang), reply_markup=kb)
    return CONTACT_TIME


async def contact_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})
    text = (update.message.text or "").strip()

    if is_cancel(text, lang):
        await update.message.reply_text(
            t("contact_canceled", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if is_back(text, lang):
        kb = back_cancel_keyboard(lang)
        await update.message.reply_text(t("question_ask", lang), reply_markup=kb)
        return CONTACT_QUESTION

    if text.lower().strip() in {"напишу свой вариант"}:
        kb = ReplyKeyboardMarkup(
            [[t("btn_cancel", lang)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(
            t("time_freeform", lang),
            reply_markup=kb,
        )
        return CONTACT_TIME

    lead["time"] = text

    kb = ReplyKeyboardMarkup(
        [
            ["📞 Звонок", "💬 Telegram"],
            ["💬 WhatsApp"],
            [t("btn_back", lang), t("btn_cancel", lang)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(t("method_ask", lang), reply_markup=kb)
    return CONTACT_METHOD


async def contact_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})
    text = (update.message.text or "").strip()

    if is_cancel(text, lang):
        await update.message.reply_text(
            t("contact_canceled", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if is_back(text, lang):
        kb = ReplyKeyboardMarkup(
            [
                ["Утром", "Днём"],
                ["Вечером", "Не принципиально"],
                [t("btn_back", lang), t("btn_cancel", lang)],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(t("time_ask", lang), reply_markup=kb)
        return CONTACT_TIME

    lead["method"] = text

    return await contact_show_summary(update, context)


def build_confirm_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t("btn_confirm_send", lang)],
            [t("btn_confirm_edit", lang)],
            [t("btn_confirm_cancel", lang)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def contact_show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})

    summary_lines = [
        t("contact_summary", lang),
        f"{t('summary_name', lang)}: {lead.get('name', '-')}",
        f"{t('summary_phone', lang)}: {lead.get('phone', '-')}",
        f"{t('summary_question', lang)}: {lead.get('question', '-')}",
        f"{t('summary_time', lang)}: {lead.get('time', '-')}",
        f"{t('summary_method', lang)}: {lead.get('method', '-')}",
        "",
        t("confirm_ask", lang),
    ]
    text = "\n".join(summary_lines)

    await update.message.reply_text(
        text,
        reply_markup=build_confirm_keyboard(lang),
    )
    return CONTACT_CONFIRM


async def contact_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})
    text = (update.message.text or "").strip()

    if text == t("btn_confirm_cancel", lang) or is_cancel(text, lang):
        await update.message.reply_text(
            t("contact_canceled", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if text == t("btn_confirm_send", lang):
        if OWNER_CHAT_ID:
            user = update.effective_user
            msg_lines = [
                t("lead_sent_owner_title", lang),
                "",
                f"{t('summary_name', lang)}: {lead.get('name', '-')}",
                f"{t('summary_phone', lang)}: {lead.get('phone', '-')}",
                f"{t('summary_question', lang)}: {lead.get('question', '-')}",
                f"{t('summary_time', lang)}: {lead.get('time', '-')}",
                f"{t('summary_method', lang)}: {lead.get('method', '-')}",
                "",
                f"User ID: {user.id}",
                f"Username: @{user.username}" if user.username else "Username: -",
            ]
            await update.get_bot().send_message(
                chat_id=OWNER_CHAT_ID,
                text="\n".join(msg_lines),
            )

        await update.message.reply_text(
            t("lead_sent_user", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if text == t("btn_confirm_edit", lang):
        # упрощённо — начинаем заново
        context.user_data.pop("lead", None)
        return await contact_start(update, context)

    await update.message.reply_text(
        t("confirm_ask", lang),
        reply_markup=build_confirm_keyboard(lang),
    )
    return CONTACT_CONFIRM


# ---------- FAQ для пациентов ----------

def build_patient_faq_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("1. Кому нужен скрининг?", callback_data="faq_who")],
        [InlineKeyboardButton("2. Когда его лучше делать?", callback_data="faq_when")],
        [InlineKeyboardButton("3. Что показывает анализ?", callback_data="faq_what")],
        [InlineKeyboardButton("4. Если мы оба носители?", callback_data="faq_both")],
        [
            InlineKeyboardButton(
                "5. Чем отличается от обычных анализов крови?", callback_data="faq_diff"
            )
        ],
        [
            InlineKeyboardButton(
                "6. «У нас хорошая генетика, это не про нас?»", callback_data="faq_good_bad"
            )
        ],
        [
            InlineKeyboardButton(
                "7. Как сдаётся анализ и сколько это занимает?", callback_data="faq_how_long"
            )
        ],
        [InlineKeyboardButton("⬅️ Назад в главное меню", callback_data="faq_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def faq_menu_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update)
    text = t("faq_menu_title", lang)
    reply_markup = build_patient_faq_keyboard()

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=reply_markup)


import os
import logging
from typing import Dict, Any

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
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

# ---------- логирование ----------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logger.info("🚀 Bot started: test commit from VS Code")

# ---------- токены / ID ----------

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "0"))

(
    CONTACT_NAME,
    CONTACT_PHONE,
    CONTACT_QUESTION,
    CONTACT_TIME,
    CONTACT_METHOD,
    CONTACT_CONFIRM,
    CONTACT_EDIT,
) = range(7)


# ---------- утилиты ----------

def get_lang(update: Update) -> str:
    """Определяем язык по Telegram-профилю (ru / en)."""
    user = update.effective_user
    code = (user.language_code or "").lower() if user else ""
    if code.startswith("ru"):
        return "ru"
    return "en"


def t(label: str, lang: str = "ru") -> str:
    """Простейшая i18n-табличка."""
    texts = {
        "greeting": {
            "ru": (
                "Привет! Я бот по скринингу на носительство наследственных заболеваний.\n\n"
                "Чем могу помочь?"
            ),
            "en": (
                "Hi! I'm a bot about carrier screening for inherited diseases.\n\n"
                "How can I help you?"
            ),
        },
        "main_menu_title": {
            "ru": "Выберите раздел:",
            "en": "Choose a section:",
        },
        "btn_plan": {
            "ru": "👶 Планируем / ждём ребёнка",
            "en": "👶 Planning / expecting a baby",
        },
        "btn_doctor": {
            "ru": "👨‍⚕️ Я врач",
            "en": "👨‍⚕️ I am a doctor",
        },
        "btn_contact": {
            "ru": "📝 Записаться / Оставить контакты",
            "en": "📝 Leave contacts / book a call",
        },
        "btn_faq": {
            "ru": "❓ FAQ",
            "en": "❓ FAQ",
        },
        "btn_back": {
            "ru": "⬅️ Назад",
            "en": "⬅️ Back",
        },
        "btn_cancel": {
            "ru": "❌ Отмена",
            "en": "❌ Cancel",
        },
        "name_ask": {
            "ru": "Как к вам обращаться? (имя или имя + фамилия)",
            "en": "How should I call you? (name or full name)",
        },
        "phone_ask": {
            "ru": "Напишите, пожалуйста, номер телефона для связи:",
            "en": "Please send your phone number (with country code, e.g. +7…):",
        },
        "phone_invalid": {
            "ru": (
                "Похоже, номер в непривычном формате.\n\n"
                "Пожалуйста, введите номер телефона в привычном формате, например:\n"
                "+7 999 123-45-67 или 8 999 123-45-67."
            ),
            "en": (
                "This doesn’t look like a valid phone number.\n"
                "Please send it in a format like +7 999 123-45-67."
            ),
        },
        "question_ask": {
            "ru": (
                "Кратко опишите, какой у вас вопрос?\n"
                "(например: планирование беременности, скрининг на носительство, консультация генетика)"
            ),
            "en": "Briefly describe your question or situation.",
        },
        "time_ask": {
            "ru": "Когда вам удобно поговорить?\nВыберите вариант или напишите свой:",
            "en": "When is it convenient to talk? Choose an option or type your own:",
        },
        "time_freeform": {
            "ru": "Укажите удобное время для связи в свободной форме:",
            "en": "Please specify a convenient time in free form:",
        },
        "method_ask": {
            "ru": "Как удобнее с вами связаться?",
            "en": "How would you like us to contact you?",
        },
        "contact_canceled": {
            "ru": (
                "Заявка отменена. Если передумаете — просто нажмите снова "
                "«Записаться / Оставить контакты»."
            ),
            "en": (
                "Request cancelled. If you change your mind, just press "
                "“Leave contacts / book a call” again."
            ),
        },
        "contact_summary": {
            "ru": "Проверьте, всё ли верно:\n\n",
            "en": "Please check your data:\n\n",
        },
        "summary_name": {
            "ru": "Имя",
            "en": "Name",
        },
        "summary_phone": {
            "ru": "Телефон",
            "en": "Phone",
        },
        "summary_question": {
            "ru": "Вопрос",
            "en": "Question",
        },
        "summary_time": {
            "ru": "Удобное время",
            "en": "Preferred time",
        },
        "summary_method": {
            "ru": "Способ связи",
            "en": "Contact method",
        },
        "confirm_ask": {
            "ru": (
                "Если всё верно — отправляем заявку?\n\n"
                "Вы можете отправить, изменить данные или отменить."
            ),
            "en": (
                "If everything is correct, should we send your request?\n\n"
                "You can send, edit data or cancel."
            ),
        },
        "btn_confirm_send": {
            "ru": "✅ Всё верно, отправить",
            "en": "✅ Send",
        },
        "btn_confirm_edit": {
            "ru": "✏️ Изменить данные",
            "en": "✏️ Edit data",
        },
        "btn_confirm_cancel": {
            "ru": "❌ Отмена",
            "en": "❌ Cancel",
        },
        "edit_what": {
            "ru": "Что хотите изменить?",
            "en": "What would you like to change?",
        },
        "btn_edit_name": {
            "ru": "Имя",
            "en": "Name",
        },
        "btn_edit_phone": {
            "ru": "Телефон",
            "en": "Phone",
        },
        "btn_edit_question": {
            "ru": "Вопрос",
            "en": "Question",
        },
        "btn_edit_time": {
            "ru": "Время",
            "en": "Time",
        },
        "btn_edit_method": {
            "ru": "Способ связи",
            "en": "Contact method",
        },
        "lead_sent_user": {
            "ru": "Готово! Я передал вашу заявку. С вами свяжутся в ближайшее время.",
            "en": "Done! Your request has been sent. We will contact you soon.",
        },
        "lead_sent_owner_title": {
            "ru": "📬 НОВАЯ ЗАЯВКА ОТ ПОЛЬЗОВАТЕЛЯ",
            "en": "📬 NEW LEAD FROM USER",
        },
        "unknown_command": {
            "ru": "Я пока не знаю, что с этим сделать. Используйте кнопки меню ниже.",
            "en": "I don’t know what to do with this yet. Please use the menu buttons below.",
        },
        "faq_menu_title": {
            "ru": "❓ *FAQ по скринингу на носительство*\n\nВыберите интересующий вопрос:",
            "en": "❓ *FAQ about carrier screening*\n\nChoose a question:",
        },
        "faq_doctor_title": {
            "ru": "👨‍⚕️ *FAQ для врачей*\n\nВыберите вопрос:",
            "en": "👨‍⚕️ *FAQ for doctors*\n\nChoose a question:",
        },
        "doctor_intro": {
            "ru": (
                "Раздел для врачей. Здесь — рациональное зерно:\n"
                "когда направлять на скрининг, как объяснять пациентам и как использовать результат.\n\n"
                "Выберите вопрос ниже."
            ),
            "en": (
                "Section for doctors: when to refer, how to explain carrier screening "
                "and how to use the results.\n\nChoose a question below."
            ),
        },
    }
    return texts.get(label, {}).get(lang, texts.get(label, {}).get("ru", label))


def main_menu_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t("btn_plan", lang)],
            [t("btn_doctor", lang)],
            [t("btn_contact", lang)],
            [t("btn_faq", lang)],
        ],
        resize_keyboard=True,
    )


def back_cancel_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[t("btn_back", lang), t("btn_cancel", lang)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def is_back(text: str, lang: str) -> bool:
    return text.strip() == t("btn_back", lang)


def is_cancel(text: str, lang: str) -> bool:
    return text.strip() == t("btn_cancel", lang)


def is_valid_phone(phone: str) -> bool:
    """
    Простая проверка телефона:
    - считаем только цифры
    - минимум 10 цифр
    - первая цифра 7 или 8
    """
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 10:
        return False
    if digits[0] not in ("7", "8"):
        return False
    return True


# ---------- главное меню ----------

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update)
    msg = update.message or update.callback_query.message  # type: ignore
    await msg.reply_text(
        t("main_menu_title", lang),
        reply_markup=main_menu_keyboard(lang),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update)
    await update.message.reply_text(
        t("greeting", lang),
        reply_markup=main_menu_keyboard(lang),
    )


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update)
    text = (update.message.text or "").strip()

    if text == t("btn_plan", lang):
        msg = (
            "👶 Раздел для пар, которые планируют беременность или ждут ребёнка.\n\n"
            "Скрининг на носительство помогает заранее понять генетические риски "
            "и при необходимости обсудить варианты с врачом-генетиком.\n\n"
            "Если хотите, оставьте контакты — и с вами свяжутся для детального разбора."
        )
        await update.message.reply_text(msg)

    elif text == t("btn_doctor", lang):
        await doctor_faq_menu_entry(update, context)

    elif text == t("btn_contact", lang):
        return await contact_start(update, context)

    elif text == t("btn_faq", lang):
        await faq_menu_entry(update, context)

    else:
        await update.message.reply_text(
            t("unknown_command", lang),
            reply_markup=main_menu_keyboard(lang),
        )


# ---------- контактная форма ----------

async def contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_lang(update)
    context.user_data["lang"] = lang
    context.user_data.setdefault("lead", {})
    context.user_data.pop("editing_field", None)

    kb = ReplyKeyboardMarkup(
        [[t("btn_cancel", lang)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(t("name_ask", lang), reply_markup=kb)
    return CONTACT_NAME


async def contact_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})
    text = (update.message.text or "").strip()

    if is_cancel(text, lang):
        await update.message.reply_text(
            t("contact_canceled", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    lead["name"] = text

    kb = back_cancel_keyboard(lang)
    await update.message.reply_text(t("phone_ask", lang), reply_markup=kb)
    return CONTACT_PHONE


async def contact_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})
    text = (update.message.text or "").strip()

    if is_cancel(text, lang):
        await update.message.reply_text(
            t("contact_canceled", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if is_back(text, lang):
        kb = ReplyKeyboardMarkup(
            [[t("btn_cancel", lang)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(t("name_ask", lang), reply_markup=kb)
        return CONTACT_NAME

    if not is_valid_phone(text):
        await update.message.reply_text(
            t("phone_invalid", lang),
            reply_markup=back_cancel_keyboard(lang),
        )
        return CONTACT_PHONE

    lead["phone"] = text

    kb = back_cancel_keyboard(lang)
    await update.message.reply_text(t("question_ask", lang), reply_markup=kb)
    return CONTACT_QUESTION


async def contact_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})
    text = (update.message.text or "").strip()

    if is_cancel(text, lang):
        await update.message.reply_text(
            t("contact_canceled", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if is_back(text, lang):
        kb = back_cancel_keyboard(lang)
        await update.message.reply_text(t("phone_ask", lang), reply_markup=kb)
        return CONTACT_PHONE

    lead["question"] = text

    kb = ReplyKeyboardMarkup(
        [
            ["Утром", "Днём"],
            ["Вечером", "Не принципиально"],
            [t("btn_back", lang), t("btn_cancel", lang)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(t("time_ask", lang), reply_markup=kb)
    return CONTACT_TIME


async def contact_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})
    text = (update.message.text or "").strip()

    if is_cancel(text, lang):
        await update.message.reply_text(
            t("contact_canceled", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if is_back(text, lang):
        kb = back_cancel_keyboard(lang)
        await update.message.reply_text(t("question_ask", lang), reply_markup=kb)
        return CONTACT_QUESTION

    # Допускаем свободный ввод времени
    lead["time"] = text

    kb = ReplyKeyboardMarkup(
        [
            ["📞 Звонок", "💬 Telegram"],
            ["💬 WhatsApp"],
            [t("btn_back", lang), t("btn_cancel", lang)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(t("method_ask", lang), reply_markup=kb)
    return CONTACT_METHOD


async def contact_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})
    text = (update.message.text or "").strip()

    if is_cancel(text, lang):
        await update.message.reply_text(
            t("contact_canceled", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if is_back(text, lang):
        kb = ReplyKeyboardMarkup(
            [
                ["Утром", "Днём"],
                ["Вечером", "Не принципиально"],
                [t("btn_back", lang), t("btn_cancel", lang)],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(t("time_ask", lang), reply_markup=kb)
        return CONTACT_TIME

    lead["method"] = text

    return await contact_show_summary(update, context)


def build_confirm_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t("btn_confirm_send", lang)],
            [t("btn_confirm_edit", lang)],
            [t("btn_confirm_cancel", lang)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def contact_show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})

    summary_lines = [
        t("contact_summary", lang),
        f"{t('summary_name', lang)}: {lead.get('name', '-')}",
        f"{t('summary_phone', lang)}: {lead.get('phone', '-')}",
        f"{t('summary_question', lang)}: {lead.get('question', '-')}",
        f"{t('summary_time', lang)}: {lead.get('time', '-')}",
        f"{t('summary_method', lang)}: {lead.get('method', '-')}",
        "",
        t("confirm_ask", lang),
    ]
    text = "\n".join(summary_lines)

    await update.message.reply_text(
        text,
        reply_markup=build_confirm_keyboard(lang),
    )
    return CONTACT_CONFIRM


async def contact_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", get_lang(update))
    lead: Dict[str, Any] = context.user_data.setdefault("lead", {})
    text = (update.message.text or "").strip()

    if text == t("btn_confirm_cancel", lang) or is_cancel(text, lang):
        await update.message.reply_text(
            t("contact_canceled", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if text == t("btn_confirm_send", lang):
        if OWNER_CHAT_ID:
            user = update.effective_user
            msg_lines = [
                t("lead_sent_owner_title", lang),
                "",
                f"{t('summary_name', lang)}: {lead.get('name', '-')}",
                f"{t('summary_phone', lang)}: {lead.get('phone', '-')}",
                f"{t('summary_question', lang)}: {lead.get('question', '-')}",
                f"{t('summary_time', lang)}: {lead.get('time', '-')}",
                f"{t('summary_method', lang)}: {lead.get('method', '-')}",
                "",
                f"User ID: {user.id}",
                f"Username: @{user.username}" if user.username else "Username: -",
            ]
            await update.get_bot().send_message(
                chat_id=OWNER_CHAT_ID,
                text="\n".join(msg_lines),
            )

        await update.message.reply_text(
            t("lead_sent_user", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if text == t("btn_confirm_edit", lang):
        # Упрощённый вариант — заполнить всё заново
        context.user_data.pop("lead", None)
        return await contact_start(update, context)

    await update.message.reply_text(
        t("confirm_ask", lang),
        reply_markup=build_confirm_keyboard(lang),
    )
    return CONTACT_CONFIRM


# ---------- FAQ для пациентов ----------

def build_patient_faq_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("1. Кому нужен скрининг?", callback_data="faq_who")],
        [InlineKeyboardButton("2. Когда его лучше делать?", callback_data="faq_when")],
        [InlineKeyboardButton("3. Что показывает анализ?", callback_data="faq_what")],
        [InlineKeyboardButton("4. Если мы оба носители?", callback_data="faq_both")],
        [
            InlineKeyboardButton(
                "5. Чем отличается от обычных анализов крови?", callback_data="faq_diff"
            )
        ],
        [
            InlineKeyboardButton(
                "6. «У нас хорошая генетика?»", callback_data="faq_good_bad"
            )
        ],
        [InlineKeyboardButton("7. Как сдаётся анализ?", callback_data="faq_how_long")],
        [InlineKeyboardButton("8. Это ведь очень дорогой анализ...", callback_data="faq_cost")],
        [InlineKeyboardButton("⬅️ Назад в главное меню", callback_data="faq_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def faq_menu_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update)
    text = t("faq_menu_title", lang)
    reply_markup = build_patient_faq_keyboard()

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=reply_markup)


async def faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update)
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "faq_back":
        await query.edit_message_text("Возвращаемся в главное меню…")
        await show_main_menu(update, context)
        return

    if data == "faq_who":
        text = (
            "1️⃣ *Кому нужен скрининг на носительство?*\n\n"
            "— Парам, которые планируют беременность.\n"
            "— Семьям, где уже есть ребёнок с наследственным заболеванием.\n"
            "— Тем, у кого в роду были непонятные тяжёлые заболевания, ранняя детская смертность "
            "или невынашивание беременности.\n"
            "— Близкородственные браки — *особенно!*\n\n"
            "Даже если «все здоровы», каждый человек является носителем мутаций — "
            "это не болезнь и по самочувствию это не видно."
        )

    elif data == "faq_when":
        text = (
            "2️⃣ *Когда лучше делать скрининг?*\n\n"
            "Идеально — до наступления беременности, на этапе планирования.\n\n"
            "Но сделать его можно и во время беременности, и перед ЭКО, и в донорских программах.\n"
            "Чем раньше вы узнаете о рисках, тем больше у вас будет вариантов для спокойного решения."
        )

    elif data == "faq_what":
        text = (
            "3️⃣ *Что показывает анализ?*\n\n"
            "Анализ показывает, являетесь ли вы и/или партнёр носителем мутаций, "
            "которые повышают риск рождения ребёнка с тяжёлым наследственным заболеванием.\n\n"
            "Если оба родителя — носители одной и той же мутации, риск больного ребёнка — "
            "*25% для каждой беременности*, даже если в семье уже есть здоровые дети."
        )

    elif data == "faq_both":
        text = (
            "4️⃣ *Если мы оба носители — это приговор?*\n\n"
            "Нет. Это значит, что есть высокий риск, но есть и варианты решений:\n"
            "— ЭКО с преимплантационной генетической диагностикой (ПГТ);\n"
            "— использование донорского материала;\n"
            "— пренатальная генетическая диагностика (если уже беременны);\n"
            "— осознанное решение о беременности с пониманием рисков.\n\n"
            "Ключевое — не оставаться с результатом один на один, а обсудить его с врачом-генетиком."
        )

    elif data == "faq_diff":
        text = (
            "5️⃣ *Чем Скрининг на носительство отличается от обычных анализов крови?*\n\n"
            "Обычные анализы смотрят текущее состояние организма.\n\n"
            "Скрининг на носительство — ДНК-исследование. Он не ищет болезнь у вас, а отвечает на вопрос:\n"
            "«есть ли у нас риск передать нашему ребёнку тяжёлое наследственное заболевание?». "
            "Большинство таких заболеваний, к сожалению, до сих пор неизлечимы."
        )

    elif data == "faq_good_bad":
        text = (
            "6️⃣ *«У нас хорошая генетика, это не про нас?»*\n\n"
            "Каждый человек несёт несколько «тихих» мутаций — они никак не проявляются.\n"
            "Проблема возникает только тогда, когда одинаковая мутация встречается у обоих партнёров.\n\n"
            "Поэтому отсутствие видимых болезней в семье не равно отсутствию наследственных рисков.\n"
            "Если брак близкородственный — такое исследование особенно необходимо."
        )

    elif data == "faq_how_long":
        text = (
            "7️⃣ *Как сдаётся анализ и сколько это занимает?*\n\n"
            "— Как правило, это забор крови из вены в пробирку с EDTA (2–4 ml).\n"
            "— Подготовки не требуется, *НЕ НАТОЩАК*, в любое время.\n"
            "— Лучше не есть жирного и не пить алкоголь за 3–4 часа до сдачи.\n"
            "— Результат готов от нескольких дней до нескольких недель (в зависимости от анализа).\n\n"
            "Дальше результат обсуждают с врачом-генетиком — чтобы понять, что он значит именно для вашей семьи."
        )

    elif data == "faq_cost":
        text = (
            "8️⃣ *Это ведь очень дорогой анализ...*\n\n"
            "— Да. Анализ стоит недёшево. Но его достаточно сдать один раз, и он остаётся актуальным для пары на всю жизнь.\n\n"
            "— Если рассуждать о цене, то стоит также подумать о том, что находится *«на другой чаше весов»* — "
            "**спокойствие, понимание рисков и возможность осознанного выбора**.\n\n"
            "— Расскажите это — про *«дорогой анализ»* — родителям детей с тяжёлыми генетическими заболеваниями?\n"
            "  Думаете, они не отдали бы всё, если бы могли вернуть время назад и **узнать заранее** о таком анализе?\n\n"
            "— Чтобы не сомневаться — пройдите **консультацию врача-генетика**.\n"
            "  Это доступнее, консультация длится *45–60+ минут* и даёт вам **полное понимание** и ясность."
        )

    else:
        text = "Выберите пункт из меню ниже."

    await query.edit_message_text(text, reply_markup=build_patient_faq_keyboard())


# ---------- FAQ для врачей ----------

def build_doctor_faq_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "1. Кого направлять на скрининг в первую очередь?",
                callback_data="dfaq_who",
            )
        ],
        [
            InlineKeyboardButton(
                "2. Как объяснить пациентам смысл скрининга?",
                callback_data="dfaq_explain",
            )
        ],
        [
            InlineKeyboardButton(
                "3. Что делать с парой-носителями?",
                callback_data="dfaq_both",
            )
        ],
        [
            InlineKeyboardButton(
                "4. Нужна ли консультация генетика до и после?",
                callback_data="dfaq_geneticist",
            )
        ],
        [
            InlineKeyboardButton(
                "5. Как результат скрининга помогает в реальной практике?",
                callback_data="dfaq_practice",
            )
        ],
        [InlineKeyboardButton("⬅️ Назад в главное меню", callback_data="dfaq_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def doctor_faq_menu_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update)
    text = t("faq_doctor_title", lang) + "\n\n" + t("doctor_intro", lang)
    kb = build_doctor_faq_keyboard()

    if update.message:
        await update.message.reply_text(text, reply_markup=kb)
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=kb)


async def doctor_faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update)
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "dfaq_back":
        await query.edit_message_text("Возвращаемся в главное меню…")
        await show_main_menu(update, context)
        return

    if data == "dfaq_who":
        text = (
            "1️⃣ *Кого направлять на скрининг в первую очередь?*\n\n"
            "— Пары на этапе прегравидарной подготовки и перед ЭКО.\n"
            "— Пары с отягощённым семейным анамнезом (дети с НЗ, ранняя детская смертность).\n"
            "— Пациенты из популяционных групп с повышенной частотой отдельных заболеваний.\n\n"
            "По сути — любую пару, которая задумывается о планировании беременности и готова "
            "к ответственному информированному выбору."
        )
    elif data == "dfaq_explain":
        text = (
            "2️⃣ *Как объяснить пациенту смысл скрининга?*\n\n"
            "Рабочая формула: «Мы не ищем болезнь у вас. Мы смотрим, не являетесь ли вы носителями "
            "генетических вариантов, которые при совпадении у партнёров могут передаться ребёнку».\n\n"
            "Важно подчеркнуть, что носительство — не диагноз, а повод грамотно спланировать беременность."
        )
    elif data == "dfaq_both":
        text = (
            "3️⃣ *Что делать с парой-носителями?*\n\n"
            "Рекомендовано обсуждение с врачом-генетиком. Возможные опции:\n"
            "— ЭКО с ПГТ;\n"
            "— донорские программы;\n"
            "— естественная беременность с пониманием риска и возможностью пренатальной диагностики.\n\n"
            "Ключевое — донести, что пара не обязана выбирать «правильный» сценарий, но должна понимать риски."
        )
    elif data == "dfaq_geneticist":
        text = (
            "4️⃣ *Нужна ли консультация генетика до и после скрининга?*\n\n"
            "Желательна до — чтобы объяснить пациентам цели и ограничения исследования.\n"
            "Обязательна после выявления клинически значимых мутаций или совпадения носительства у партнёров.\n\n"
            "Именно генетик должен интерпретировать результаты и помогать в выборе дальнейшей тактики."
        )
    elif data == "dfaq_practice":
        text = (
            "5️⃣ *Как результат скрининга помогает в реальной практике?*\n\n"
            "— Позволяет заранее выявить пары с высоким риском тяжёлых НЗ и предложить им альтернативные пути.\n"
            "— Снижает число «неожиданных» случаев тяжёлых заболеваний у детей.\n"
            "— Повышает доверие пациентов: они видят, что им предлагают современный превентивный подход.\n\n"
            "По сути, это инструмент стратификации риска и более осознанного репродуктивного выбора."
        )
    else:
        text = "Выберите вопрос из меню ниже."

    await query.edit_message_text(text, reply_markup=build_doctor_faq_keyboard())


# ---------- main ----------

def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN в переменных окружения.")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    # Диалог по сбору контактов
    contact_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                lambda u, c: contact_start(u, c)
                if (
                    u.message
                    and u.message.text
                    and u.message.text.strip()
                    in (
                        t("btn_contact", get_lang(u)),
                    )
                )
                else ConversationHandler.END,
            )
        ],
        states={
            CONTACT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_name)],
            CONTACT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_phone)],
            CONTACT_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contact_question)
            ],
            CONTACT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_time)],
            CONTACT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_method)],
            CONTACT_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contact_confirm)
            ],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    application.add_handler(contact_conv)

    # Обработка текстов главного меню
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
    )

    # Callback-и для FAQ
    application.add_handler(CallbackQueryHandler(faq_answer, pattern=r"^faq_"))
    application.add_handler(CallbackQueryHandler(doctor_faq_answer, pattern=r"^dfaq_"))

    application.run_polling()


if __name__ == "__main__":
    main()


# ---------- FAQ для врачей ----------

def build_doctor_faq_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "1. Кого направлять на скрининг в первую очередь?",
                callback_data="dfaq_who",
            )
        ],
        [
            InlineKeyboardButton(
                "2. Как объяснить пациентам смысл скрининга?",
                callback_data="dfaq_explain",
            )
        ],
        [
            InlineKeyboardButton(
                "3. Что делать с парой-носителями?",
                callback_data="dfaq_both",
            )
        ],
        [
            InlineKeyboardButton(
                "4. Нужна ли консультация генетика до и после?",
                callback_data="dfaq_geneticist",
            )
        ],
        [
            InlineKeyboardButton(
                "5. Как результат скрининга помогает в реальной практике?",
                callback_data="dfaq_practice",
            )
        ],
        [InlineKeyboardButton("⬅️ Назад в главное меню", callback_data="dfaq_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def doctor_faq_menu_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update)
    text = t("faq_doctor_title", lang) + "\n\n" + t("doctor_intro", lang)
    kb = build_doctor_faq_keyboard()

    if update.message:
        await update.message.reply_text(text, reply_markup=kb)
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=kb)


async def doctor_faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(update)
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "dfaq_back":
        await query.edit_message_text("Возвращаемся в главное меню…")
        await show_main_menu(update, context)
        return

    if data == "dfaq_who":
        text = (
            "1️⃣ *Кого направлять на скрининг в первую очередь?*\n\n"
            "— Пары на этапе прегравидарной подготовки и перед ЭКО.\n"
            "— Пары с отягощённым семейным анамнезом (дети с НЗ, ранняя детская смертность).\n"
            "— Пациенты из популяционных групп с повышенной частотой отдельных заболеваний.\n\n"
            "По сути — любую пару, которая задумывается о планировании беременности и готова "
            "к ответственному информированному выбору."
        )
    elif data == "dfaq_explain":
        text = (
            "2️⃣ *Как объяснить пациенту смысл скрининга?*\n\n"
            "Рабочая формула: «Мы не ищем болезнь у вас. Мы смотрим, не являетесь ли вы носителями "
            "генетических вариантов, которые при совпадении у партнёров могут передаться ребёнку».\n\n"
            "Важно подчеркнуть, что носительство — не диагноз, а повод грамотно спланировать беременность."
        )
    elif data == "dfaq_both":
        text = (
            "3️⃣ *Что делать с парой-носителями?*\n\n"
            "Рекомендовано обсуждение с врачом-генетиком. Возможные опции:\n"
            "— ЭКО с ПГТ;\n"
            "— донорские программы;\n"
            "— естественная беременность с пониманием риска и возможностью пренатальной диагностики.\n\n"
            "Ключевое — донести, что пара не обязана выбирать «правильный» сценарий, но должна понимать риски."
        )
    elif data == "dfaq_geneticist":
        text = (
            "4️⃣ *Нужна ли консультация генетика до и после скрининга?*\n\n"
            "Желательна до — чтобы объяснить пациентам цели и ограничение исследования.\n"
            "Обязательна после выявления клинически значимых мутаций или совпадения носительства у партнёров.\n\n"
            "Именно генетик должен интерпретировать результаты и помогать в выборе дальнейшей тактики."
        )
    elif data == "dfaq_practice":
        text = (
            "5️⃣ *Как результат скрининга помогает в реальной практике?*\n\n"
            "— Позволяет заранее выявить пары с высоким риском тяжёлых НЗ и предложить им альтернативные пути.\n"
            "— Снижает число «неожиданных» случаев тяжёлых заболеваний у детей.\n"
            "— Повышает доверие пациентов: они видят, что им предлагают современный превентивный подход.\n\n"
            "По сути, это инструмент стратификации риска и более осознанного репродуктивного выбора."
        )
    else:
        text = "Выберите вопрос из меню ниже."

    await query.edit_message_text(text, reply_markup=build_doctor_faq_keyboard())


# ---------- main ----------

def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN в переменных окружения.")

    application = Application.builder().token(BOT_TOKEN).build()

    # /start
    application.add_handler(CommandHandler("start", start))

    # contact conversation: запускается только по нажатию на кнопку "Записаться / Оставить контакты"
    from re import escape
    pattern_contact = rf"^{escape(t('btn_contact', 'ru'))}$|^{escape(t('btn_contact', 'en'))}$"

    contact_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(pattern_contact),
                contact_start,
            )
        ],
        states={
            CONTACT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_name)],
            CONTACT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_phone)],
            CONTACT_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_question)],
            CONTACT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_time)],
            CONTACT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_method)],
            CONTACT_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_confirm)],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    application.add_handler(contact_conv)

    # обработчик остальных текстов — главное меню
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
    )

    # FAQ callbacks
    application.add_handler(CallbackQueryHandler(faq_answer, pattern=r"^faq_"))
    application.add_handler(CallbackQueryHandler(doctor_faq_answer, pattern=r"^dfaq_"))

    application.run_polling()


if __name__ == "__main__":
    main()
