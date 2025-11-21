import os
import re
import logging
from typing import Dict, Any, List

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
            "ru": "Раздел для врачей: когда направлять, как объяснять пациентам и как использовать результаты.\n",
            "en": "For doctors: when to refer, how to explain screening and how to use the results.\n",
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
            "Скрининг помогает заранее узнать генетические риски.\n\n"
            "Если хотите — оставьте контакты, и мы свяжемся с вами для обсуждения."
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

    await update.message.reply_text(
        t("question_ask", lang),
        reply_markup=back_cancel_keyboard(lang),
    )
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
# FAQ — ПАЦИЕНТЫ (ЛЕГКО РАСШИРЯЕМЫЙ)
# ---------------------------------------------------------------------

FAQ_PATIENT_LIST: List[Dict[str, str]] = [
    {
        "id": "who",
        "title": "1️⃣ Кому нужен скрининг?",
        "answer": (
            "1️⃣ *Кому нужен скрининг на носительство?*\n\n"
            "— Парам, которые планируют беременность.\n"
            "— Семьям, где уже есть ребёнок с наследственным заболеванием.\n"
            "— Тем, у кого в роду были тяжёлые заболевания, ранняя детская смерть, невынашивание.\n"
            "— Близкородственные браки — *особенно*.\n\n"
            "Даже если «все здоровы», каждый человек является носителем мутаций — "
            "по самочувствию это не видно."
        ),
    },
    {
        "id": "when",
        "title": "2️⃣ Когда лучше делать?",
        "answer": (
            "2️⃣ *Когда лучше делать скрининг?*\n\n"
            "Идеально — до наступления беременности, на этапе планирования.\n\n"
            "Можно и во время беременности, и перед ЭКО, и в донорских программах.\n\n"
            "Чем раньше вы узнаёте о рисках, тем больше у вас вариантов для спокойного решения."
        ),
    },
    {
        "id": "what",
        "title": "3️⃣ Что показывает анализ?",
        "answer": (
            "3️⃣ *Что показывает анализ?*\n\n"
            "Анализ показывает, являетесь ли вы и/или партнёр носителем мутаций, "
            "которые повышают риск рождения ребёнка с тяжёлым наследственным заболеванием.\n\n"
            "Если оба родителя — носители одной и той же мутации, риск больного ребёнка — "
            "*25% для каждой беременности*, даже если в семье уже есть здоровые дети."
        ),
    },
    {
        "id": "both",
        "title": "4️⃣ Если мы оба носители?",
        "answer": (
            "4️⃣ *Если мы оба носители — это приговор?*\n\n"
            "Нет. Это значит, что риск выше, но есть варианты решений:\n\n"
            "— ЭКО с преимплантационной генетической диагностикой (ПГТ);\n"
            "— использование донорского материала;\n"
            "— пренатальная генетическая диагностика (если уже беременны);\n"
            "— осознанное решение о беременности с пониманием рисков.\n\n"
            "Главное — не оставаться с результатом один на один, а обсудить его с врачом-генетиком."
        ),
    },
    {
        "id": "diff",
        "title": "5️⃣ Чем отличается от обычных анализов?",
        "answer": (
            "5️⃣ *Чем скрининг на носительство отличается от обычных анализов крови?*\n\n"
            "Обычные анализы показывают текущее состояние организма.\n\n"
            "Скрининг на носительство — это ДНК-исследование. "
            "Он не ищет болезнь у вас, а отвечает на вопрос:\n\n"
            "«Есть ли у нас риск передать нашему ребёнку тяжёлое наследственное заболевание?».\n\n"
            "Большинство таких заболеваний до сих пор, к сожалению, неизлечимы."
        ),
    },
    {
        "id": "good",
        "title": "6️⃣ «У нас хорошая генетика…»",
        "answer": (
            "6️⃣ *«У нас хорошая генетика, это не про нас?»*\n\n"
            "Каждый человек несёт несколько «тихих» мутаций — они никак не проявляются.\n"
            "Проблема возникает, когда одинаковая мутация встречается у обоих партнёров.\n\n"
            "Поэтому отсутствие видимых болезней в семье не означает отсутствия наследственных рисков.\n"
            "Если брак близкородственный — такое исследование особенно важно."
        ),
    },
    {
        "id": "how",
        "title": "7️⃣ Как сдаётся и сроки?",
        "answer": (
            "7️⃣ *Как сдаётся анализ и сколько это занимает?*\n\n"
            "— Обычно это кровь из вены в пробирку с EDTA (2–4 ml).\n"
            "— Подготовка не требуется, анализ *НЕ НАТОЩАК*.\n"
            "— Лучше не есть жирного и не употреблять алкоголь за 3–4 часа.\n"
            "— Результат — от нескольких дней до нескольких недель (зависит от анализа).\n\n"
            "Дальше результат обсуждают с врачом-генетиком — чтобы понять, что он значит именно для вашей семьи."
        ),
    },
    {
        "id": "cost",
        "title": "8️⃣ Это ведь очень дорогой анализ...",
        "answer": (
            "8️⃣ *Это ведь очень дорогой анализ...*\n\n"
            "— Да, анализ стоит недёшево. Но его достаточно сдать один раз, и он остаётся актуальным для пары на всю жизнь.\n\n"
            "— Если рассуждать о цене, то стоит также подумать о том, что находится *«на другой чаше весов»* — "
            "**спокойствие, понимание рисков и возможность осознанного выбора**.\n\n"
            "— Расскажите это — про *«дорогой анализ»* — родителям детей с тяжёлыми генетическими заболеваниями? "
            "Думаете, они не отдали бы всё, если бы могли вернуть время назад и **узнать заранее** о таком анализе?\n\n"
            "— Чтобы не сомневаться — пройдите **консультацию врача-генетика**. "
            "Это доступнее, консультация длится *45–60+ минут* и даёт вам **полное понимание** и ясность."
        ),
    },
]


def build_patient_faq_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(item["title"], callback_data=f"faq_{item['id']}")]
        for item in FAQ_PATIENT_LIST
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Назад в главное меню", callback_data="faq_back")])
    return InlineKeyboardMarkup(keyboard)


async def faq_menu_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    text = t("faq_menu_title", lang)
    markup = build_patient_faq_keyboard()

    if update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        q = update.callback_query
        await q.answer()
        await q.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")


async def faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "faq_back":
        return await show_main_menu(update, context)

    faq_id = data.replace("faq_", "", 1)
    item = next((x for x in FAQ_PATIENT_LIST if x["id"] == faq_id), None)

    if not item:
        await query.edit_message_text(
            "Не удалось найти этот вопрос. Попробуйте выбрать из меню ниже.",
            reply_markup=build_patient_faq_keyboard(),
        )
        return

    await query.edit_message_text(
        item["answer"],
        reply_markup=build_patient_faq_keyboard(),
        parse_mode="Markdown",
    )


# ---------------------------------------------------------------------
# FAQ — ВРАЧИ (ТОЖЕ РАСШИРЯЕМЫЙ)
# ---------------------------------------------------------------------

DOCTOR_FAQ_LIST: List[Dict[str, str]] = [
    {
        "id": "who",
        "title": "1️⃣ Кого направлять?",
        "answer": (
            "1️⃣ *Кого направлять на скрининг в первую очередь?*\n\n"
            "— Пары на этапе прегравидарной подготовки и перед ЭКО.\n"
            "— Пары с отягощённым семейным анамнезом (дети с НЗ, ранняя детская смертность).\n"
            "— Пациенты из популяционных групп с повышенной частотой отдельных заболеваний.\n\n"
            "По сути — любую пару, которая задумывается о планировании беременности и готова к "
            "ответственному информированному выбору."
        ),
    },
    {
        "id": "explain",
        "title": "2️⃣ Как объяснить пациенту?",
        "answer": (
            "2️⃣ *Как объяснить пациенту смысл скрининга?*\n\n"
            "Рабочая формула: «Мы не ищем болезнь у вас. Мы смотрим, не являетесь ли вы носителями "
            "генетических вариантов, которые при совпадении у партнёров могут передаться ребёнку».\n\n"
            "Важно подчеркнуть, что носительство — не диагноз, а повод грамотно спланировать беременность."
        ),
    },
    {
        "id": "both",
        "title": "3️⃣ Что делать с парой-носителями?",
        "answer": (
            "3️⃣ *Что делать с парой-носителями?*\n\n"
            "Рекомендовано обсуждение с врачом-генетиком. Возможные опции:\n\n"
            "— ЭКО с ПГТ;\n"
            "— донорские программы;\n"
            "— естественная беременность с пониманием риска и возможностью пренатальной диагностики.\n\n"
            "Ключевое — донести, что пара не обязана выбирать «правильный» сценарий, но должна понимать риски."
        ),
    },
    {
        "id": "geneticist",
        "title": "4️⃣ Консультация до/после?",
        "answer": (
            "4️⃣ *Нужна ли консультация генетика до и после скрининга?*\n\n"
            "Желательна до — чтобы объяснить пациентам цели и ограничения исследования.\n"
            "Обязательна после выявления клинически значимых мутаций или совпадения носительства у партнёров.\n\n"
            "Именно генетик должен интерпретировать результаты и помогать в выборе дальнейшей тактики."
        ),
    },
    {
        "id": "practice",
        "title": "5️⃣ Польза в реальной практике",
        "answer": (
            "5️⃣ *Как результат скрининга помогает в реальной практике?*\n\n"
            "— Позволяет заранее выявить пары с высоким риском тяжёлых НЗ и предложить им альтернативные пути.\n"
            "— Снижает число «неожиданных» случаев тяжёлых заболеваний у детей.\n"
            "— Повышает доверие пациентов: они видят, что им предлагают современный превентивный подход.\n\n"
            "По сути — это инструмент стратификации риска и более осознанного репродуктивного выбора."
        ),
    },
    {
        "id": "cooperation",
        "title": "6️⃣ Запрос на сотрудничество",
        "answer": (
            "6️⃣ *Могу ли получить Метод лист по генетическим комплексам для прегравидарной подготовки?*\n\n"
            "Да. Вы можете получить Методический лист по генетическим комплексам для прегравидарной подготовки.\n\n"
            "Оставьте, пожалуйста, Ваши контактные данные в форме ниже, "
            "и я пришлю вам всю необходимую информацию."
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
        await q.answer()
        await q.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")


async def doctor_faq_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "dfaq_back":
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


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN!")

    app = Application.builder().token(BOT_TOKEN).build()

    from re import escape
    pattern = rf"^{escape(t('btn_contact', 'ru'))}$|^{escape(t('btn_contact', 'en'))}$"

    contact_conv = ConversationHandler(
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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(contact_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))
    app.add_handler(CallbackQueryHandler(faq_answer, pattern=r"^faq_"))
    app.add_handler(CallbackQueryHandler(doctor_faq_answer, pattern=r"^dfaq_"))

    app.run_polling()


if __name__ == "__main__":
    main()
