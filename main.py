
# -*- coding: utf-8 -*-
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
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "0"))

def t(label: str) -> str:
    texts = {
        "greeting": "Привет! Я бот по скринингу на носительство наследственных заболеваний.\n\nЧем могу помочь?",
        "btn_plan": "👶 Планируем / ждём ребёнка",
        "btn_doctor": "👨‍⚕️ Я врач",
        "btn_contact": "📝 Записаться / Оставить контакты",
        "btn_free_question": "/Написать свой вопрос",
        "btn_faq": "❓ FAQ",
        "free_explain": "Можете написать свой вопрос прямо здесь.",
        "free_received": "Я передал ваше сообщение. Можно продолжать писать здесь, в боте — ответы будут приходить в этот же чат.",
        "choose_contact": "Как оставить контакт?",
        "leave_phone": "📱 Оставить номер телефона",
        "leave_username": "💬 Использовать мой @username",
        "send_phone_button": "📱 Отправить номер телефона",
        "phone_saved": "Спасибо! Я сохранил ваш номер.",
        "username_saved": "Спасибо! Я сохранил ваш @username.",
        "no_username": "У вас не установлен username в Telegram. Пожалуйста, оставьте номер телефона.",
        "done": "Готово! Возвращаю вас в главное меню."
    }
    return texts[label]

def main_menu():
    return ReplyKeyboardMarkup(
        [
            [t("btn_plan")],
            [t("btn_doctor")],
            [t("btn_contact"), t("btn_free_question")],
            [t("btn_faq")],
        ],
        resize_keyboard=True,
    )

FREE_CONTACT = range(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t("greeting"), reply_markup=main_menu())

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text

    if txt == t("btn_free_question"):
        context.user_data["free_mode"] = True
        return await update.message.reply_text(t("free_explain"), reply_markup=main_menu())

    if context.user_data.get("free_mode"):
        return await forward_free(update, context)

    return await update.message.reply_text("Используйте меню ниже.", reply_markup=main_menu())

async def forward_free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""

    # send to owner
    if OWNER_CHAT_ID:
        msg = f"💬 Новое сообщение:\n\nUser ID: {user.id}\nUsername: @{user.username}\n\n{text}"
        await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=msg)

    # reply to user
    await update.message.reply_text(t("free_received"))

    # inline keyboard: choose contact method
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("leave_phone"), callback_data="free_phone")],
        [InlineKeyboardButton(t("leave_username"), callback_data="free_username")],
    ])
    await update.message.reply_text(t("choose_contact"), reply_markup=kb)

async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user

    if data == "free_phone":
        # send reply keyboard with request_contact
        kb = ReplyKeyboardMarkup(
            [[KeyboardButton(t("send_phone_button"), request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await query.message.reply_text("Нажмите кнопку ниже, чтобы отправить номер телефона:", reply_markup=kb)
        return

    if data == "free_username":
        if not user.username:
            await query.answer()
            await query.message.reply_text(t("no_username"))
            return
        # save username
        if OWNER_CHAT_ID:
            await context.bot.send_message(OWNER_CHAT_ID, f"Контакт от @{user.username}")
        await query.message.reply_text(t("username_saved"), reply_markup=main_menu())
        context.user_data["free_mode"] = False
        return

async def contact_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
        if OWNER_CHAT_ID:
            user = update.effective_user
            await context.bot.send_message(OWNER_CHAT_ID, f"Телефон от {user.id}: {phone}")
        await update.message.reply_text(t("phone_saved"), reply_markup=main_menu())
        context.user_data["free_mode"] = False

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.CONTACT, contact_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

    app.run_polling()

if __name__ == "__main__":
    main()
