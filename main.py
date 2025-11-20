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
# НАСТРОЙКИ / ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# I18N / ТЕКСТЫ
# ---------------------------------------------------------------------

def get_lang(update: Update) -> str:
    """Определяем язык Telegram-профиля."""
    user = update.effective_user
    code = (user.language_code or "").lower() if user else ""
    return "ru" if code.startswith("ru") else "en"


def t(label: str, lang: str = "ru") -> str:
    """Простая таблица переводов."""
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
        "main_menu_title": {"ru": "Выберите раздел:", "en": "Choose a section:"},
        "btn_plan": {"ru": "👶 Планируем / ждём ребёнка", "en": "👶 Planning / expecting a baby"},
        "btn_doctor": {"ru": "👨‍⚕️ Я врач", "en": "👨‍⚕️ I am a doctor"},
        "btn_contact": {"ru": "📝 Записаться / Оставить контакты", "en": "📝 Leave contacts / book a call"},
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
                "Похоже, номер в непривычном формате 🤔\n\n"
                "Пожалуйста, отправьте номер *цифрами*, например: `+7 999 123-45-67`."
            ),
            "en": (
                "This doesn’t look like a valid phone number 🤔\n\n"
                "Please send your phone *using digits*, e.g. `+1 202 555 0119`."
            ),
        },

        "question_ask": {
            "ru": (
                "Кратко опишите, какой у вас вопрос?\n"
                "(например: планирование беременности, скрининг на носительство, консультация генетика)"
            ),
            "en": "Briefly describe your question.",
        },

        "time_ask": {
            "ru": "Когда вам удобно поговорить? Выберите вариант или напишите свой:",
            "en": "When is it convenient to talk? Choose or type your own:",
        },

        "time_freeform": {
            "ru": "Укажите удобное время в свободной форме:",
            "en": "Specify time in free form:",
        },

        "method_ask": {"ru": "Как удобнее связаться?", "en": "Preferred contact method:"},

        "contact_canceled": {
            "ru": "Заявка отменена. Чтобы начать снова — нажмите «Записаться / Оставить контакты».",
            "en": "Request cancelled. To try again, press “Leave contacts / book a call”.",
        },

        "contact_summary": {"ru": "Проверьте данные:\n", "en": "Please check your data:\n"},
        "summary_name": {"ru": "Имя", "en": "Name"},
        "summary_phone": {"ru": "Телефон", "en": "Phone"},
        "summary_question": {"ru": "Вопрос", "en": "Question"},
        "summary_time": {"ru": "Удобное время", "en": "Preferred time"},
        "summary_method": {"ru": "Способ связи", "en": "Contact method"},

        "confirm_ask": {
            "ru": "Отправляем заявку? Можно отправить, изменить данные или отменить.",
            "en": "Send request? You may send, edit or cancel.",
        },

        "btn_confirm_send": {"ru": "✅ Отправить", "en": "✅ Send"},
        "btn_confirm_edit": {"ru": "✏️ Изменить", "en": "✏️ Edit"},
        "btn_confirm_cancel": {"ru": "❌ Отмена", "en": "❌ Cancel"},

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
                "Раздел для врачей: когда направлять, как объяснять пациентам и как использовать результаты.\n"
            ),
            "en": (
                "For doctors: when to refer, how to explain screening and how to use the results.\n"
            ),
        },
    }
    return texts.get(label, {}).get(lang, texts.get(label, {}).get("ru", label))


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
        [[t("btn_back", lang), t("btn_cancel", lang)]],
        resize_keyboard=True,
    )


def is_back(txt: str, lang: str) -> bool:
    return txt == t("btn_back", lang)


def is_cancel(txt: str, lang: str) -> bool:
    return txt == t("btn_cancel", lang)


def is_valid_phone(phone: str) -> bool:
    """Минимум 10 цифр."""
    digits = re.findall(r"\d", phone)
    return len(digits) >= 10


# ---------------------------------------------------------------------
# ГЛАВНОЕ МЕНЮ
# ---------------------------------------------------------------------

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


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = update.message.text.strip()

    if text == t("btn_plan", lang):
        await update.message.reply_text(
            "👶 Раздел для пар, которые планируют беременность.\n\n"
            "Скрининг помогает заранее узнать генетические риски. "
            "При желании — оставьте контакты, и мы свяжемся с вами."
        )

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


# ---------------------------------------------------------------------
# КОНТАКТНАЯ ФОРМА
# ---------------------------------------------------------------------

async def contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    context.user_data["lang"] = lang
    context.user_data["lead"] = {}

    await update.message.reply_text(
        t("name_ask", lang),
        reply_markup=ReplyKeyboardMarkup([[t("btn_cancel", lang)]], resize_keyboard=True),
    )
    return CONTACT_NAME


async def contact_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    txt = update.message.text.strip()

    if is_cancel(txt, lang):
        return await cancel_contact(update)

    context.user_data["lead"]["name"] = txt

    await update.message.reply_text(
        t("phone_ask", lang),
        reply_markup=back_cancel_keyboard(lang),
    )
    return CONTACT_PHONE


async def contact_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    txt = update.message.text.strip()

    if is_cancel(txt, lang):
        return await cancel_contact(update)
    if is_back(txt, lang):
        return await contact_start(update, context)

    if not is_valid_phone(txt):
        await update.message.reply_text(
            t("phone_invalid", lang),
            parse_mode="Markdown",
            reply_markup=back_cancel_keyboard(lang),
        )
        return CONTACT_PHONE

    context.user_data["lead"]["phone"] = txt

    await update.message.reply_text(t("question_ask", lang), reply_markup=back_cancel_keyboard(lang))
    return CONTACT_QUESTION


async def contact_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    txt = update.message.text.strip()

    if is_cancel(txt, lang):
        return await cancel_contact(update)
    if is_back(txt, lang):
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

    if is_cancel(txt, lang):
        return await cancel_contact(update)
    if is_back(txt, lang):
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
    await update.message.reply_text(t("method_ask", lang), reply_markup=kb)
    return CONTACT_METHOD


async def contact_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    txt = update.message.text.strip()

    if is_cancel(txt, lang):
        return await cancel_contact(update)
    if is_back(txt, lang):
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
    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=ReplyKeyboardMarkup(
            [
                [t("btn_confirm_send", lang)],
                [t("btn_confirm_edit", lang)],
                [t("btn_confirm_cancel", lang)],
            ],
            resize_keyboard=True,
        ),
    )
    return CONTACT_CONFIRM


async def cancel_contact(update: Update):
    lang = get_lang(update)
    await update.message.reply_text(t("contact_canceled", lang), reply_markup=None)
    return ConversationHandler.END


async def contact_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    txt = update.message.text.strip()
    lead = context.user_data["lead"]

    if txt == t("btn_confirm_cancel", lang):
        return await cancel_contact(update)

    if txt == t("btn_confirm_edit", lang):
        return await contact_start(update, context)

    if txt == t("btn_confirm_send", lang):
        await send_lead(update, lang, lead)
        await update.message.reply_text(
            t("lead_sent_user", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    return CONTACT_CONFIRM


async def send_lead(update: Update, lang: str, lead: Dict[str, Any]):
    """Отправка заявки владельцу."""
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
# FAQ — ПАЦИЕНТЫ
# ---------------------------------------------------------------------

def patient_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1. Кому нужен скрининг?", callback_data="faq_who")],
        [InlineKeyboardButton("2. Когда его лучше делать?", callback_data="faq_when")],
        [InlineKeyboardButton("3. Что показывает анализ?", callback_data="faq_what")],
        [InlineKeyboardButton("4. Если мы оба носители?", callback_data="faq_both")],
        [InlineKeyboardButton("5. Чем отличается?", callback_data="faq_diff")],
        [InlineKeyboardButton("6. «У нас хорошая генетика?»", callback_data="faq_good")],
        [InlineKeyboardButton("7. Как сдаётся и сроки?", callback_data="faq_how")],
        [InlineKeyboardButton("8. Это ведь очень дорогой анализ...", callback_data="faq_cost")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="faq_back")],
    ])


FAQ_PATIENT_TEXTS = {
    "faq_who": (
        "1️⃣ *Кому нужен скрининг?*\n\n"
        "— Парам, планирующим беременность.\n"
        "— Семьям с ребёнком с наследственным заболеванием.\n"
        "— При тяжёлых заболеваниях в роду, ранних смертях, невынашивании.\n"
        "— Близкородственные браки — *особенно*.\n\n"
        "Каждый человек является носителем мутаций — это не болезнь."
    ),

    "faq_when": (
        "2️⃣ *Когда лучше делать скрининг?*\n\n"
        "Идеально — до беременности.\n"
        "Можно во время беременности и перед ЭКО.\n"
        "Чем раньше вы знаете — тем больше у вас вариантов."
    ),

    "faq_what": (
        "3️⃣ *Что показывает анализ?*\n\n"
        "Показывает, являетесь ли вы/партнёр носителем мутаций, которые могут привести "
        "к тяжёлому наследственному заболеванию у ребёнка.\n\n"
        "Если оба — носители одной мутации, риск — *25% в каждой беременности*."
    ),

    "faq_both": (
        "4️⃣ *Если мы оба носители — это приговор?*\n\n"
        "Нет. Опции:\n"
        "— ЭКО + ПГТ\n"
        "— донорские программы\n"
        "— пренатальная диагностика\n"
        "— осознанное решение с пониманием рисков.\n\n"
        "Результаты нужно обсудить с врачом-генетиком."
    ),

    "faq_diff": (
        "5️⃣ *Чем отличается от обычных анализов?*\n\n"
        "Это ДНК-исследование. Не ищет болезнь, а оценивает риск рождения ребёнка "
        "с тяжёлым наследственным заболеванием."
    ),

    "faq_good": (
        "6️⃣ *«У нас хорошая генетика, это не про нас?»*\n\n"
        "Каждый человек несёт несколько «тихих» мутаций. "
        "Проблема возникает только при совпадении у партнёров.\n\n"
        "Отсутствие болезней в семье ≠ отсутствие рисков."
    ),

    "faq_how": (
        "7️⃣ *Как сдаётся анализ и сколько занимает?*\n\n"
        "— Кровь из вены в пробирку EDTA 2–4 ml.\n"
        "— *НЕ НАТОЩАК*, без подготовки.\n"
        "— Лучше без алкоголя/жирного за 3–4 часа.\n"
        "— Срок: от нескольких дней до нескольких недель.\n\n"
        "Далее — обсуждение с генетиком."
    ),

    "faq_cost": (
        "8️⃣ *Это ведь очень дорогой анализ...*\n\n"
        "— Да, недёшево. Но сдаётся один раз и остаётся актуальным всю жизнь.\n\n"
        "— Если рассуждать о цене — подумайте, что находится *«на другой чаше весов»*: "
        "**спокойствие, понимание рисков и возможность осознанного выбора**.\n\n"
        "— Расскажите это — про *«дорогой анализ»* — родителям детей с тяжёлыми наследственными "
        "заболеваниями? Думаете, они бы не отдали всё, чтобы **узнать заранее**?\n\n"
        "— Чтобы не сомневаться — пройдите **консультацию врача-генетика**. "
        "Это доступнее, длится *45–60+ минут* и даёт вам **полное понимание**."
    ),
}


async def faq_menu_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = t("faq_menu_title", lang)

    if update.message:
        await update.message.reply_text(text, reply_markup=patient_keyboard(), parse_mode="Markdown")
    else:
        q = update.callback_query
        await q.answer()
        await q.edit_message_text(text, reply_markup=patient_keyboard(), parse_mode="Markdown")


async def faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    key = query.data
    if key == "faq_back":
        return await show_main_menu(update, context)

    text = FAQ_PATIENT_TEXTS.get(key, "Выберите вопрос из меню.")
    await query.edit_message_text(text, reply_markup=patient_keyboard(), parse_mode="Markdown")


# ---------------------------------------------------------------------
# FAQ — ВРАЧИ
# ---------------------------------------------------------------------

DOCTOR_FAQ_TEXTS = {
    "dfaq_who": (
        "1️⃣ *Кого направлять в первую очередь?*\n\n"
        "— Пары перед ЭКО\n"
        "— пары с плохим семейным анамнезом\n"
        "— группы риска\n\n"
        "По сути — любую пару, планирующую беременность."
    ),
    "dfaq_explain": (
        "2️⃣ *Как объяснить пациенту?*\n\n"
        "Мы не ищем болезнь. Мы смотрим, не носители ли они одинаковой мутации, "
        "которая может передаться ребёнку."
    ),
    "dfaq_both": (
        "3️⃣ *Что делать с парой-носителями?*\n\n"
        "Консультация генетика обязательна. Опции:\n"
        "— ЭКО+ПГТ\n"
        "— донорство\n"
        "— естественная беременность с пониманием риска."
    ),
    "dfaq_geneticist": (
        "4️⃣ *Нужна ли консультация до / после?*\n\n"
        "До — желательно.\n"
        "После выявления мутаций — обязательно."
    ),
    "dfaq_practice": (
        "5️⃣ *Чем помогает на практике?*\n\n"
        "— выявляет пары высокого риска\n"
        "— снижает число тяжёлых НЗ\n"
        "— повышает доверие пациентов"
    ),
}


def doctor_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1. Кого направлять?", callback_data="dfaq_who")],
        [InlineKeyboardButton("2. Как объяснить?", callback_data="dfaq_explain")],
        [InlineKeyboardButton("3. Пара-носители", callback_data="dfaq_both")],
        [InlineKeyboardButton("4. Консультация до/после", callback_data="dfaq_geneticist")],
        [InlineKeyboardButton("5. Польза на практике", callback_data="dfaq_practice")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="dfaq_back")],
    ])


async def doctor_faq_menu_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = t("faq_doctor_title", lang) + t("doctor_intro", lang)

    if update.message:
        await update.message.reply_text(text, reply_markup=doctor_keyboard(), parse_mode="Markdown")
    else:
        q = update.callback_query
        await q.answer()
        await q.edit_message_text(text, reply_markup=doctor_keyboard(), parse_mode="Markdown")


async def doctor_faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    key = query.data
    if key == "dfaq_back":
        return await show_main_menu(update, context)

    text = DOCTOR_FAQ_TEXTS.get(key, "Выберите пункт меню.")
    await query.edit_message_text(text, reply_markup=doctor_keyboard(), parse_mode="Markdown")


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN!")

    app = Application.builder().token(BOT_TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", start))

    # ---------------- CONTACT CONVERSATION ----------------
    from re import escape
    pattern = rf"^{escape(t('btn_contact', 'ru'))}$|^{escape(t('btn_contact', 'en'))}$"

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(pattern), contact_start)],
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
    app.add_handler(conv)

    # Всё остальное → главное меню
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))

    # FAQ
    app.add_handler(CallbackQueryHandler(faq_answer, pattern=r"^faq_"))
    app.add_handler(CallbackQueryHandler(doctor_faq_answer, pattern=r"^dfaq_"))

    app.run_polling()


if __name__ == "__main__":
    main()
