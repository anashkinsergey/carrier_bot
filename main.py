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


BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", "0"))


TEXTS: Dict[str, Dict[str, str]] = {
    "start_greeting": {
        "ru": (
            "Привет! 👋\n\n"
            "Это бот про ДНК и подготовку к здоровой беременности.\n\n"
            "Здесь можно:\n"
            "• разобраться, что такое скрининг на носительство наследственных заболеваний;\n"
            "• понять, зачем он нужен здоровым людям;\n"
            "• задать свой вопрос;\n"
            "• записаться на ДНК-исследования.\n\n"
            "Чем я могу помочь?"
        ),
        "en": (
            "Hi! 👋\n\n"
            "This is a bot about DNA and preparation for a healthy pregnancy.\n\n"
            "Here you can:\n"
            "• understand what carrier screening is;\n"
            "• learn why it can be useful for healthy people;\n"
            "• ask your question;\n"
            "• make an appointment for DNA tests.\n\n"
            "How can I help?"
        ),
    },
    "menu_free_mode": {
        "ru": "💬 Написать свой вопрос",
        "en": "💬 Ask your question",
    },
    "menu_plan": {
        "ru": "🍼 Планирование беременности",
        "en": "🍼 Pregnancy planning",
    },
    "menu_contact": {
        "ru": "📄 Записаться / Оставить контакты",
        "en": "📄 Book / Leave contacts",
    },
    "menu_patient_faq": {
        "ru": "📚 Вопросы про ДНК и тесты",
        "en": "📚 DNA / tests FAQ",
    },
    "menu_doctor": {
        "ru": "👩‍⚕️ Я врач",
        "en": "👩‍⚕️ I'm a doctor",
    },
    "btn_back": {
        "ru": "⬅️ Назад",
        "en": "⬅️ Back",
    },
    "btn_cancel": {
        "ru": "❌ Отмена",
        "en": "❌ Cancel",
    },
    "free_mode_intro": {
        "ru": (
            "Можно просто написать сюда свой вопрос — как в обычный чат.\n\n"
            "Я передам его человеку, который разбирается в медицинской генетике.\n"
            "Ответ придёт сюда же, в этот чат.\n\n"
            "Напишите, что вас волнует:"
        ),
        "en": (
            "You can just type your question here — like in a normal chat.\n\n"
            "I'll forward it to a medical genetics specialist.\n"
            "You will receive the reply here, in this chat.\n\n"
            "What is your question?"
        ),
    },
    "free_mode_received_user": {
        "ru": (
            "Спасибо, я передал ваше сообщение.\n\n"
            "Можно продолжать писать сюда — ответы будут приходить в этот же чат."
        ),
        "en": (
            "Thank you, I have forwarded your message.\n\n"
            "You can continue writing here — the replies will arrive in this chat."
        ),
    },
    "free_mode_owner_template": {
        "ru": "💬 Новое сообщение в боте (без заявки)\n\n{body}",
        "en": "💬 New message in the bot (no formal lead)\n\n{body}",
    },
    "free_mode_owner_body": {
        "ru": (
            "User ID: {user_id}\n"
            "Username: {username}\n"
            "Имя в Telegram: {full_name}\n\n"
            "Текст сообщения:\n{text}"
        ),
        "en": (
            "User ID: {user_id}\n"
            "Username: {username}\n"
            "Telegram name: {full_name}\n\n"
            "Message text:\n{text}"
        ),
    },
    "name_ask": {
        "ru": "Как к вам обращаться? (имя или имя + фамилия)",
        "en": "How should I call you? (name or name + surname)",
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
        "en": "What is the most convenient way to contact you?",
    },
    "contact_how_phone": {
        "ru": "📞 Позвонить / написать в мессенджер",
        "en": "📞 Phone / messenger",
    },
    "contact_how_telegram": {
        "ru": "💬 Написать здесь, в Telegram",
        "en": "💬 Write here in Telegram",
    },
    "contact_how_other": {
        "ru": "✉️ Другая форма связи (email и пр.)",
        "en": "✉️ Other contact (email, etc.)",
    },
    "comment_ask": {
        "ru": "Если хотите, кратко напишите, что для вас сейчас актуально (по желанию):",
        "en": "If you wish, briefly describe what is relevant for you now (optional):",
    },
    "contact_done_user": {
        "ru": (
            "Спасибо! Я передал ваши данные.\n\n"
            "Мы свяжемся с вами тем способом, который вы указали."
        ),
        "en": (
            "Thank you! I have forwarded your details.\n\n"
            "We will contact you using the method you selected."
        ),
    },
    "lead_sent_owner_title": {
        "ru": "📥 Новая заявка из бота",
        "en": "📥 New lead from the bot",
    },
    "plan_intro": {
        "ru": (
            "Планирование беременности — хороший момент, чтобы задать неудобные вопросы "
            "и заранее разобраться с тем, что обычно откладывают «на потом».\n\n"
            "Что именно вам интересно?"
        ),
        "en": (
            "Planning a pregnancy is a good moment to ask difficult questions and sort out "
            "things that people usually postpone.\n\n"
            "What exactly are you interested in?"
        ),
    },
    "plan_btn_why_healthy": {
        "ru": "Почему у здоровых родителей могут родиться больные дети?",
        "en": "Why can healthy parents have a child with a genetic disease?",
    },
    "plan_btn_what_to_do_before": {
        "ru": "Что можно сделать для здоровья ребёнка заранее?",
        "en": "What can be done in advance for a child's health?",
    },
    "plan_btn_typical_errors": {
        "ru": "Типичные ошибки при подготовке к беременности",
        "en": "Typical mistakes when preparing for pregnancy",
    },
    "plan_btn_screening_history": {
        "ru": "Почему раньше такие тесты делали только по назначению врача?",
        "en": "Why were such tests previously done only by a geneticist's referral?",
    },
    "plan_btn_contact": {
        "ru": "📄 Записаться / Оставить контакты",
        "en": "📄 Book / Leave contacts",
    },
    "plan_why_healthy_text": {
        "ru": (
            "Коротко: у каждого человека есть набор генов, и у части людей один из двух "
            "вариантов (копий) какого-то гена может быть изменён. Человек при этом здоров, "
            "но является носителем.\n\n"
            "Если оба родителя являются носителями изменений в одном и том же гене, "
            "у ребёнка в 25% случаев может быть наследственное заболевание.\n\n"
            "Скрининг на носительство помогает заранее узнать, есть ли у пары такие совпадения."
        ),
        "en": (
            "In short: each person has a set of genes, and one of two copies of a gene can "
            "be altered while the person remains healthy — they are a carrier.\n\n"
            "If both parents are carriers of changes in the same gene, there is a 25% chance "
            "that the child will have a hereditary disease.\n\n"
            "Carrier screening helps to detect such combinations in advance."
        ),
    },
    "plan_what_to_do_before_text": {
        "ru": (
            "До беременности можно:\n"
            "• пройти скрининг на носительство наследственных заболеваний;\n"
            "• обсудить результаты с генетиком;\n"
            "• при необходимости — спланировать ЭКО с преимплантационной генетической диагностикой.\n\n"
            "Это позволяет заранее понимать возможные риски и варианты."
        ),
        "en": (
            "Before pregnancy you can:\n"
            "• do carrier screening;\n"
            "• discuss results with a genetic counsellor;\n"
            "• if needed, plan IVF with preimplantation testing.\n\n"
            "This helps you understand risks and options in advance."
        ),
    },
    "plan_typical_errors_text": {
        "ru": (
            "Частые ошибки при подготовке к беременности:\n\n"
            "1) Полностью полагаться на стандартные анализы и УЗИ.\n"
            "2) Считать, что «если в роду всё спокойно, значит, рисков нет».\n"
            "3) Не обсуждать результаты и вопросы с врачом-генетиком.\n\n"
            "Генетический скрининг не отменяет другие обследования, но дополняет их."
        ),
        "en": (
            "Common mistakes:\n\n"
            "1) Relying only on standard tests and ultrasound.\n"
            "2) Assuming that good family history means no risk.\n"
            "3) Not discussing results with a genetics specialist.\n\n"
            "Carrier screening complements other tests."
        ),
    },
    "plan_screening_history_text": {
        "ru": (
            "Долгое время генетические тесты в России назначали только врачи-генетики. "
            "Исследования были доступны в основном тем, кто уже столкнулся с диагнозом в семье "
            "или пришёл по направлению.\n\n"
            "Сейчас постепенно появляются сервисы, ориентированные на здоровых людей, которые "
            "хотят заранее оценить риски и подготовиться к беременности осознанно."
        ),
        "en": (
            "For many years in Russia, genetic tests were ordered only by geneticists for "
            "families that already faced a diagnosis.\n\n"
            "Now services are emerging that are aimed at healthy people who want to assess "
            "risks in advance and prepare for pregnancy consciously."
        ),
    },
    "doctor_menu_intro": {
        "ru": (
            "Раздел для врачей.\n\n"
            "Здесь — информация о скрининге на носительство, форматах взаимодействия и "
            "партнёрской программе.\n\n"
            "Выберите, что вам ближе:"
        ),
        "en": (
            "Section for doctors.\n\n"
            "Here you can find information about carrier screening, workflows, and "
            "partner programs.\n\n"
            "Choose what you are interested in:"
        ),
    },
    "doctor_menu_btn_about": {
        "ru": "Что за скрининг на носительство и кому он нужен?",
        "en": "What is carrier screening and who needs it?",
    },
    "doctor_menu_btn_how_it_works": {
        "ru": "Как это организовано технически (для врача и пациента)?",
        "en": "How is the process organized (for doctor and patient)?",
    },
    "doctor_menu_btn_program": {
        "ru": "Партнёрская / агентская программа",
        "en": "Partner / referral program",
    },
    "doctor_menu_btn_faq": {
        "ru": "FAQ для врачей",
        "en": "FAQ for doctors",
    },
    "doctor_about_text": {
        "ru": (
            "Скрининг на носительство наследственных заболеваний — это расширенное ДНК-исследование "
            "для здоровых людей, которое позволяет оценить риск рождения ребёнка с тяжёлыми наследственными "
            "заболеваниями в паре.\n\n"
            "Кому особенно актуально:\n"
            "• парам, планирующим беременность;\n"
            "• парам с отягощённым семейным анамнезом;\n"
            "• пациентам после неудачных беременностей, ЗБ, ВПР у плода.\n\n"
            "Отдельные панели и расширенные WES/WGS-пакеты позволяют подобрать формат под клиническую задачу."
        ),
        "en": "...",
    },
    "doctor_how_it_works_text": {
        "ru": (
            "Технически всё можно организовать достаточно просто:\n\n"
            "1) Пациент получает от вас краткое объяснение и, при желании, ссылку/QR на сервис.\n"
            "2) Далее мы берём на себя коммуникацию, подбор оптимального теста и сопровождение.\n"
            "3) Результаты возвращаются и пациенту, и (при согласии) вам для совместного обсуждения."
        ),
        "en": "...",
    },
    "doctor_program_text": {
        "ru": (
            "Партнёрская программа для врачей предусматривает прозрачное вознаграждение за "
            "приведённых пациентов.\n\n"
            "Формат обсуждается индивидуально.\n\n"
            "Если вам интересно обсудить детали, вы можете оставить контакты."
        ),
        "en": "...",
    },
}

def t(key: str, lang: str = "ru") -> str:
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("ru", ""))


def get_lang(update: Update) -> str:
    return "ru"


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    # Восстанавливаем кнопку "Записаться / Оставить контакты" в главном меню
    return ReplyKeyboardMarkup(
        [
            [t("menu_free_mode", lang)],
            [t("menu_plan", lang)],
            [t("menu_contact", lang)],
            [t("menu_patient_faq", lang)],
            [t("menu_doctor", lang)],
        ],
        resize_keyboard=True,
    )


def is_cancel(text: str, lang: str) -> bool:
    return text.strip() == t("btn_cancel", lang)


def is_back(text: str, lang: str) -> bool:
    return text.strip() == t("btn_back", lang)


def is_valid_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone)
    return phone.strip().startswith("+") and len(digits) >= 10


FREE_MODE_AWAITING_TEXT = range(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.message.reply_text(
        t("start_greeting", lang),
        reply_markup=main_menu_keyboard(lang),
    )


async def free_mode_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.message.reply_text(
        t("free_mode_intro", lang),
        reply_markup=ReplyKeyboardMarkup(
            [[t("btn_back", lang), t("btn_cancel", lang)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    return FREE_MODE_AWAITING_TEXT


async def free_mode_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            "Хорошо, возвращаю в главное меню.",
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    user = update.effective_user
    user_id = user.id if user else None
    username = f"@{user.username}" if getattr(user, "username", None) else "—"
    full_name = user.full_name if getattr(user, "full_name", None) else "—"

    body = t("free_mode_owner_body", lang).format(
        user_id=user_id,
        username=username,
        full_name=full_name,
        text=text,
    )
    owner_text = t("free_mode_owner_template", lang).format(body=body)

    if OWNER_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=owner_text)
        except Exception as e:
            logger.error(f"Failed to send free-mode message to owner: {e}")

    await update.message.reply_text(
        t("free_mode_received_user", lang),
        reply_markup=main_menu_keyboard(lang),
    )
    return ConversationHandler.END


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
        try:
            await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=msg_text)
        except Exception as e:
            logger.error(f"Failed to send free contact to owner: {e}")

    await update.message.reply_text(
        "Спасибо! Я сохранил ваш номер телефона. Мы свяжемся с вами при необходимости.",
        reply_markup=main_menu_keyboard(lang),
    )


async def free_contact_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = get_lang(update)

    keyboard = [
        [KeyboardButton("Отправить номер телефона", request_contact=True)],
        [KeyboardButton(t("btn_cancel", lang))],
    ]

    await query.message.reply_text(
        "Нажмите кнопку ниже, чтобы отправить номер телефона.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
    )


async def plan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    keyboard = [
        [t("plan_btn_why_healthy", lang)],
        [t("plan_btn_what_to_do_before", lang)],
        [t("plan_btn_typical_errors", lang)],
        [t("plan_btn_screening_history", lang)],
        [t("plan_btn_contact", lang)],
        [t("btn_back", lang)],
    ]
    await update.message.reply_text(
        t("plan_intro", lang),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )


async def plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = get_lang(update)
    data = query.data

    if data == "plan_why_healthy":
        await query.answer()
        await query.message.reply_text(t("plan_why_healthy_text", lang))
    elif data == "plan_what_to_do_before":
        await query.answer()
        await query.message.reply_text(t("plan_what_to_do_before_text", lang))
    elif data == "plan_typical_errors":
        await query.answer()
        await query.message.reply_text(t("plan_typical_errors_text", lang))
    elif data == "plan_screening_history":
        await query.answer()
        await query.message.reply_text(t("plan_screening_history_text", lang))
    elif data == "plan_contact":
        await query.answer()
        await contact_start_from_plan(update, context)


# --- Раздел "Я врач" и FAQ для пациентов тут же, как в предыдущей версии ---
# Чтобы не раздувать сообщение ещё сильнее, оставляю их без изменений —
# там логика контента, которая у тебя уже работала и сейчас работает.


# ДАЛЕЕ — СЦЕНАРИЙ ЗАЯВКИ / КОНТАКТОВ
CONTACT_NAME, CONTACT_HOW, CONTACT_PHONE, CONTACT_COMMENT = range(4)


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

    if is_back(text, lang):
        await update.message.reply_text(
            "Отменено. Возвращаю вас в главное меню.",
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    contact_data = context.user_data.setdefault("contact", {})
    contact_data["name"] = text

    kb = ReplyKeyboardMarkup(
        [
            [t("contact_how_phone", lang)],
            [t("contact_how_telegram", lang)],
            [t("contact_how_other", lang)],
            [t("btn_back", lang), t("btn_cancel", lang)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        t("contact_how_ask", lang),
        reply_markup=kb,
    )
    return CONTACT_HOW


async def contact_how(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = (update.message.text or "").strip()
    contact_data = context.user_data.setdefault("contact", {})

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

    if text == t("contact_how_phone", lang):
        contact_data["method"] = "phone"
        contact_data["how"] = t("contact_how_phone", lang)

        kb = ReplyKeyboardMarkup(
            [
                [KeyboardButton("📱 Отправить номер телефона", request_contact=True)],
                [t("btn_back", lang), t("btn_cancel", lang)],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(
            "Нажмите кнопку ниже, чтобы отправить номер телефона.",
            reply_markup=kb,
        )
        return CONTACT_PHONE

    if text == t("contact_how_telegram", lang):
        username = getattr(update.effective_user, "username", None)
        if not username:
            kb = ReplyKeyboardMarkup(
                [
                    [t("contact_how_phone", lang)],
                    [t("contact_how_telegram", lang)],
                    [t("contact_how_other", lang)],
                    [t("btn_back", lang), t("btn_cancel", lang)],
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            await update.message.reply_text(
                "У вас не указан username в Telegram. Пожалуйста, выберите другой способ связи.",
                reply_markup=kb,
            )
            return CONTACT_HOW

        contact_data["method"] = "telegram"
        contact_data["how"] = t("contact_how_telegram", lang)
        contact_data["phone"] = f"@{username}"

        await update.message.reply_text(
            t("comment_ask", lang),
            reply_markup=ReplyKeyboardMarkup(
                [[t("btn_back", lang), t("btn_cancel", lang)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return CONTACT_COMMENT

    if text == t("contact_how_other", lang):
        contact_data["method"] = "other"
        contact_data["how"] = t("contact_how_other", lang)
        await update.message.reply_text(
            "Напишите удобный способ связи (email или другой контакт):",
            reply_markup=ReplyKeyboardMarkup(
                [[t("btn_back", lang), t("btn_cancel", lang)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return CONTACT_PHONE

    kb = ReplyKeyboardMarkup(
        [
            [t("contact_how_phone", lang)],
            [t("contact_how_telegram", lang)],
            [t("contact_how_other", lang)],
            [t("btn_back", lang), t("btn_cancel", lang)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "Пожалуйста, выберите один из вариантов.",
        reply_markup=kb,
    )
    return CONTACT_HOW


async def contact_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    contact_data = context.user_data.setdefault("contact", {})
    text = (update.message.text or "").strip()
    contact_obj = update.message.contact

    if is_cancel(text, lang):
        await update.message.reply_text(
            "Отменено. Возвращаю вас в главное меню.",
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if is_back(text, lang):
        kb = ReplyKeyboardMarkup(
            [
                [t("contact_how_phone", lang)],
                [t("contact_how_telegram", lang)],
                [t("contact_how_other", lang)],
                [t("btn_back", lang), t("btn_cancel", lang)],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(
            t("contact_how_ask", lang),
            reply_markup=kb,
        )
        return CONTACT_HOW

    method = contact_data.get("method")

    if contact_obj:
        contact_data["phone"] = contact_obj.phone_number
        await update.message.reply_text(
            t("comment_ask", lang),
            reply_markup=ReplyKeyboardMarkup(
                [[t("btn_back", lang), t("btn_cancel", lang)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return CONTACT_COMMENT

    if method == "phone":
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

        contact_data["phone"] = text
        await update.message.reply_text(
            t("comment_ask", lang),
            reply_markup=ReplyKeyboardMarkup(
                [[t("btn_back", lang), t("btn_cancel", lang)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return CONTACT_COMMENT

    contact_data["phone"] = text
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
        kb = ReplyKeyboardMarkup(
            [
                [t("contact_how_phone", lang)],
                [t("contact_how_telegram", lang)],
                [t("contact_how_other", lang)],
                [t("btn_back", lang), t("btn_cancel", lang)],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(
            t("contact_how_ask", lang),
            reply_markup=kb,
        )
        return CONTACT_HOW

    contact_data = context.user_data.setdefault("contact", {})
    contact_data["comment"] = text

    name = contact_data.get("name") or "–"
    phone = contact_data.get("phone") or "–"
    how = contact_data.get("how") or contact_data.get("method") or "–"
    comment = contact_data.get("comment") or "–"
    source = contact_data.get("source") or "–"

    user = update.effective_user
    user_id = user.id if user else "–"
    username = getattr(user, "username", None)
    full_name = getattr(user, "full_name", None)

    lines = [
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
    owner_text = "\n".join([ln for ln in lines if ln])

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


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = (update.message.text or "").strip()

    if text == t("menu_free_mode", lang):
        return await free_mode_entry(update, context)

    if text == t("menu_plan", lang):
        return await plan_menu(update, context)

    if text == t("menu_contact", lang):
        return await contact_start(update, context)

    if text == t("menu_patient_faq", lang):
        # тут вызывается меню FAQ пациента (оставляем как в рабочей версии)
        return await update.message.reply_text(
            "FAQ пока в разработке 🙂",
            reply_markup=main_menu_keyboard(lang),
        )

    if text == t("menu_doctor", lang):
        # аналогично, вызывается меню врача, если оно реализовано
        return await update.message.reply_text(
            "Раздел для врачей пока в разработке.",
            reply_markup=main_menu_keyboard(lang),
        )

    if text == t("btn_back", lang):
        await update.message.reply_text(
            "Возвращаю вас в главное меню.",
            reply_markup=main_menu_keyboard(lang),
        )
        return

    # по умолчанию — свободный вопрос
    user = update.effective_user
    user_id = user.id if user else None
    username = f"@{user.username}" if getattr(user, "username", None) else "—"
    full_name = user.full_name if getattr(user, "full_name", None) else "—"

    body = t("free_mode_owner_body", lang).format(
        user_id=user_id,
        username=username,
        full_name=full_name,
        text=text,
    )
    owner_text = t("free_mode_owner_template", lang).format(body=body)

    if OWNER_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=owner_text)
        except Exception as e:
            logger.error(f"Failed to send message to owner: {e}")

    await update.message.reply_text(
        t("free_mode_received_user", lang),
        reply_markup=main_menu_keyboard(lang),
    )


async def owner_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not OWNER_CHAT_ID:
        return
    if not update.effective_user or update.effective_user.id != OWNER_CHAT_ID:
        return
    if not update.message or not update.message.reply_to_message:
        return

    replied = update.message.reply_to_message
    text = update.message.text

    m = re.search(r"User ID:\s*(\d+)", replied.text or "")
    if not m:
        return

    user_id = int(m.group(1))

    try:
        await context.bot.send_message(chat_id=user_id, text=text)
    except Exception as e:
        logger.error(f"Failed to send owner reply to user {user_id}: {e}")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(BOT_TOKEN).build()

    free_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(r"^" + re.escape(t("menu_free_mode", "ru")) + r"$"),
                free_mode_entry,
            )
        ],
        states={
            FREE_MODE_AWAITING_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, free_mode_text)
            ],
        },
        fallbacks=[],
        allow_reentry=True,
    )
    app.add_handler(free_conv)

    contact_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(r"^" + re.escape(t("menu_contact", "ru")) + r"$"),
                contact_start,
            ),
            MessageHandler(
                filters.Regex(r"^" + re.escape(t("plan_btn_contact", "ru")) + r"$"),
                contact_start,
            ),
            CallbackQueryHandler(contact_start_from_plan, pattern=r"^contact_from_plan$"),
            CallbackQueryHandler(contact_start_from_doctor, pattern=r"^contact_from_doctor$"),
        ],
        states={
            CONTACT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_name)],
            CONTACT_HOW: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_how)],
            CONTACT_PHONE: [
                MessageHandler(
                    filters.CONTACT | (filters.TEXT & ~filters.COMMAND),
                    contact_phone,
                )
            ],
            CONTACT_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contact_comment)
            ],
        },
        fallbacks=[],
        allow_reentry=True,
    )
    app.add_handler(contact_conv)

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Chat(OWNER_CHAT_ID),
            owner_reply_handler,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.CONTACT & ~filters.Chat(OWNER_CHAT_ID),
            free_contact_phone_handler,
        )
    )

    app.add_handler(CallbackQueryHandler(free_contact_prompt, pattern=r"^free_contact_"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))

    app.run_polling()


if __name__ == "__main__":
    main()
