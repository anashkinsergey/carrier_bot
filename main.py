import os
import re

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "0"))

(
    CONTACT_NAME,
    CONTACT_CONTACT_CHOICE,
    CONTACT_EXTRA_CONTACT,
    CONTACT_QUESTION,
    CONTACT_TIME,
    CONTACT_METHOD,
    CONTACT_CONFIRM,
) = range(7)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["👶 Планируем / ждём ребёнка"],
            ["👨‍⚕️ Я врач"],
            ["📝 Записаться / Оставить контакты", "/Написать свой вопрос"],
            ["❓ FAQ"],
        ],
        resize_keyboard=True,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот по скринингу на носительство наследственных заболеваний.\n\nЧем могу помочь?",
        reply_markup=main_menu_keyboard(),
    )


def is_valid_phone(p: str) -> bool:
    p = re.sub(r"[^\d+]", "", p)
    if not p.startswith("+"):
        return False
    digits = re.findall(r"\d", p)
    return 10 <= len(digits) <= 15


async def contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lead"] = {}
    kb = ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True)
    await update.message.reply_text("Как к вам обращаться? (имя или имя + фамилия)", reply_markup=kb)
    return CONTACT_NAME


async def contact_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt == "❌ Отмена":
        await update.message.reply_text(
            "Заявка отменена. Если не хотите оставлять контакты — просто напишите свой вопрос здесь.",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END

    context.user_data["lead"]["name"] = txt

    kb = ReplyKeyboardMarkup(
        [
            [KeyboardButton("📱 Отправить мой номер", request_contact=True)],
            ["Оставить username", "Написать другой контакт"],
            ["⬅️ Назад", "❌ Отмена"],
        ],
        resize_keyboard=True,
    )
    await update.message.reply_text("Как удобнее оставить контакт?", reply_markup=kb)
    return CONTACT_CONTACT_CHOICE


async def contact_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    txt = (msg.text or "").strip()

    if txt == "❌ Отмена":
        await update.message.reply_text(
            "Заявка отменена. Если не хотите оставлять контакты — просто напишите свой вопрос здесь.",
        )
        return ConversationHandler.END

    if txt == "⬅️ Назад":
        kb = ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True)
        await update.message.reply_text("Как к вам обращаться? (имя или имя + фамилия)", reply_markup=kb)
        return CONTACT_NAME

    lead = context.user_data["lead"]

    if msg.contact:
        lead["contact"] = msg.contact.phone_number.strip()
    elif txt == "Оставить username":
        user = msg.from_user
        lead["contact"] = f"@{user.username}" if user.username else "—"
    elif txt == "Написать другой контакт":
        kb = ReplyKeyboardMarkup([["⬅️ Назад", "❌ Отмена"]], resize_keyboard=True)
        await msg.reply_text(
            "Напишите удобный для вас контакт (телефон, мессенджер, почта):",
            reply_markup=kb,
        )
        return CONTACT_EXTRA_CONTACT
    elif is_valid_phone(txt):
        lead["contact"] = txt
    else:
        await msg.reply_text("Выберите вариант на клавиатуре или отправьте контакт.")
        return CONTACT_CONTACT_CHOICE

    kb = ReplyKeyboardMarkup([["⬅️ Назад", "❌ Отмена"]], resize_keyboard=True)
    await msg.reply_text(
        "Кратко опишите, какой у вас вопрос?",
        reply_markup=kb,
    )
    return CONTACT_QUESTION


async def contact_extra_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt == "❌ Отмена":
        await update.message.reply_text(
            "Заявка отменена. Если не хотите оставлять контакты — просто напишите свой вопрос здесь.",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END
    if txt == "⬅️ Назад":
        kb = ReplyKeyboardMarkup(
            [
                [KeyboardButton("📱 Отправить мой номер", request_contact=True)],
                ["Оставить username", "Написать другой контакт"],
                ["⬅️ Назад", "❌ Отмена"],
            ],
            resize_keyboard=True,
        )
        await update.message.reply_text("Как удобнее оставить контакт?", reply_markup=kb)
        return CONTACT_CONTACT_CHOICE

    context.user_data["lead"]["contact"] = txt
    kb = ReplyKeyboardMarkup([["⬅️ Назад", "❌ Отмена"]], resize_keyboard=True)
    await update.message.reply_text("Кратко опишите, какой у вас вопрос?", reply_markup=kb)
    return CONTACT_QUESTION


async def contact_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt == "❌ Отмена":
        await update.message.reply_text(
            "Заявка отменена. Если не хотите оставлять контакты — просто напишите свой вопрос здесь.",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END
    if txt == "⬅️ Назад":
        kb = ReplyKeyboardMarkup(
            [
                [KeyboardButton("📱 Отправить мой номер", request_contact=True)],
                ["Оставить username", "Написать другой контакт"],
                ["⬅️ Назад", "❌ Отмена"],
            ],
            resize_keyboard=True,
        )
        await update.message.reply_text("Как удобнее оставить контакт?", reply_markup=kb)
        return CONTACT_CONTACT_CHOICE

    context.user_data["lead"]["question"] = txt
    kb = ReplyKeyboardMarkup(
        [
            ["Утром", "Днём"],
            ["Вечером", "Не принципиально"],
            ["⬅️ Назад", "❌ Отмена"],
        ],
        resize_keyboard=True,
    )
    await update.message.reply_text("Когда вам удобно поговорить?", reply_markup=kb)
    return CONTACT_TIME


async def contact_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt == "❌ Отмена":
        await update.message.reply_text(
            "Заявка отменена. Если не хотите оставлять контакты — просто напишите свой вопрос здесь.",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END
    if txt == "⬅️ Назад":
        kb = ReplyKeyboardMarkup([["⬅️ Назад", "❌ Отмена"]], resize_keyboard=True)
        await update.message.reply_text("Кратко опишите, какой у вас вопрос?", reply_markup=kb)
        return CONTACT_QUESTION

    context.user_data["lead"]["time"] = txt
    kb = ReplyKeyboardMarkup(
        [
            ["📞 Звонок", "💬 Telegram"],
            ["💬 WhatsApp"],
            ["⬅️ Назад", "❌ Отмена"],
        ],
        resize_keyboard=True,
    )
    await update.message.reply_text("Как удобнее связаться?", reply_markup=kb)
    return CONTACT_METHOD


async def contact_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt == "❌ Отмена":
        await update.message.reply_text(
            "Заявка отменена. Если не хотите оставлять контакты — просто напишите свой вопрос здесь.",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END
    if txt == "⬅️ Назад":
        kb = ReplyKeyboardMarkup(
            [
                ["Утром", "Днём"],
                ["Вечером", "Не принципиально"],
                ["⬅️ Назад", "❌ Отмена"],
            ],
            resize_keyboard=True,
        )
        await update.message.reply_text("Когда вам удобно поговорить?", reply_markup=kb)
        return CONTACT_TIME

    context.user_data["lead"]["method"] = txt
    lead = context.user_data["lead"]
    kb = ReplyKeyboardMarkup(
        [["✅ Отправить", "✏️ Изменить"], ["❌ Отмена"]],
        resize_keyboard=True,
    )
    text = (
        "Проверьте данные:\n\n"
        f"Имя: {lead['name']}\n"
        f"Контакт: {lead['contact']}\n"
        f"Вопрос: {lead['question']}\n"
        f"Удобное время: {lead['time']}\n"
        f"Способ связи: {lead['method']}\n\n"
        "Отправляем заявку?"
    )
    await update.message.reply_text(text, reply_markup=kb)
    return CONTACT_CONFIRM


async def contact_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    lead = context.user_data["lead"]

    if txt == "❌ Отмена":
        await update.message.reply_text(
            "Заявка отменена. Если не хотите оставлять контакты — просто напишите свой вопрос здесь.",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END

    if txt == "✏️ Изменить":
        return await contact_start(update, context)

    if txt == "✅ Отправить":
        if OWNER_CHAT_ID:
            user = update.effective_user
            lines = [
                "📬 Новая заявка",
                "",
                f"Имя: {lead['name']}",
                f"Контакт: {lead['contact']}",
                f"Вопрос: {lead['question']}",
                f"Удобное время: {lead['time']}",
                f"Способ связи: {lead['method']}",
                "",
                f"User ID: {user.id}",
                f"Username: @{user.username}" if user.username else "Username: —",
            ]
            await context.bot.send_message(chat_id=OWNER_CHAT_ID, text="\n".join(lines))
        await update.message.reply_text(
            "Готово! Заявка отправлена. С вами свяжутся в ближайшее время.",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END

    return CONTACT_CONFIRM


async def explain_free_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Можете просто написать здесь свой вопрос в одном или нескольких сообщениях.\n\n"
        "Это можно сделать без телефона и других контактов — я всё равно передам ваши сообщения врачу.",
        reply_markup=main_menu_keyboard(),
    )


async def forward_free_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not OWNER_CHAT_ID:
        return
    user = update.effective_user
    text = update.message.text
    lines = [
        "💬 Новое сообщение в боте (без заявки)",
        "",
        f"User ID: {user.id}",
        f"Username: @{user.username}" if user.username else "Username: —",
        f"Имя: {user.full_name}",
        "",
        "Сообщение:",
        text,
    ]
    await context.bot.send_message(chat_id=OWNER_CHAT_ID, text="\n".join(lines))
    await update.message.reply_text(
        "Я передал ваше сообщение. Можно продолжать писать здесь, в боте — ответы будут приходить в этот же чат.",
        reply_markup=main_menu_keyboard(),
    )


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    if txt == "👶 Планируем / ждём ребёнка":
        await update.message.reply_text(
            "Здесь будет раздел для пар, которые планируют или ждут ребёнка.",
            reply_markup=main_menu_keyboard(),
        )
        return
    if txt == "👨‍⚕️ Я врач":
        await update.message.reply_text(
            "Здесь будет раздел для врачей.",
            reply_markup=main_menu_keyboard(),
        )
        return
    if txt == "📝 Записаться / Оставить контакты":
        return await contact_start(update, context)
    if txt == "/Написать свой вопрос":
        return await explain_free_question(update, context)
    if txt == "❓ FAQ":
        await update.message.reply_text("Здесь будет FAQ.", reply_markup=main_menu_keyboard())
        return

    # любое другое сообщение — свободный вопрос через бота
    await forward_free_message(update, context)


async def cmd_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OWNER_CHAT_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Формат: /reply USER_ID текст")
        return
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("USER_ID должен быть числом.")
        return
    text = " ".join(context.args[1:])
    await context.bot.send_message(chat_id=user_id, text=text)
    await update.message.reply_text("Сообщение отправлено.")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN!")

    app = Application.builder().token(BOT_TOKEN).build()

    contact_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Записаться / Оставить контакты$"), contact_start)],
        states={
            CONTACT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_name)],
            CONTACT_CONTACT_CHOICE: [MessageHandler(filters.ALL & ~filters.COMMAND, contact_choice)],
            CONTACT_EXTRA_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_extra_contact)],
            CONTACT_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_question)],
            CONTACT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_time)],
            CONTACT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_method)],
            CONTACT_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_confirm)],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", cmd_reply))
    app.add_handler(contact_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu))

    app.run_polling()


if __name__ == "__main__":
    main()
