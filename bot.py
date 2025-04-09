import os
import threading
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Flask-сервер для Render
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Бот працює!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app_flask.run(host="0.0.0.0", port=port)

# Запускаємо Flask у окремому потоці
threading.Thread(target=run_flask).start()

# Запитання калькулятора
questions = [
    "1. Введи вартість використаної пряжі (грн):",
    "2. Введи товаро-транспортні витрати (грн):",
    "3. Введи ціну наповнювача за 100 г (грн):",
    "4. Введи кількість витраченого наповнювача (в грамах):",
    "5. Введи вартість додаткових матеріалів (грн):",
    "6. Введи сумарну вартість друкованої продукції (грн):",
    "7. Введи вартість пакування (грн):",
    "8. Введи довжину використаної пряжі (в метрах):"
]

# Словник для зберігання відповідей користувача
users = {}

# Стартова команда
async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Розпочати розрахунок", callback_data="start_calculation")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привіт! Щоб розпочати розрахунок, натисни кнопку нижче:", reply_markup=reply_markup)

# Обробка натискання на кнопку
async def button(update, context):
    query = update.callback_query
    user_id = query.from_user.id

    if user_id not in users:
        users[user_id] = {'step': 0, 'answers': []}

    step = users[user_id]['step']
    await query.answer()
    await query.edit_message_text(text=questions[step])

# Обробка введених даних
async def handle_input(update, context):
    user_id = update.effective_user.id

    if user_id not in users:
        await update.message.reply_text("Натисни /start, щоб розпочати.")
        return

    step = users[user_id]['step']
    try:
        value = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Будь ласка, введи число.")
        return

    users[user_id]['answers'].append(value)
    users[user_id]['step'] += 1
    step = users[user_id]['step']

    if step < len(questions):
        await update.message.reply_text(questions[step])
    else:
        a = users[user_id]['answers']
        yarn_cost = a[0]
        transport = a[1]
        filler_price_per_100g = a[2]
        filler_grams = a[3]
        extras = a[4]
        printing = a[5]
        packaging = a[6]
        yarn_length = a[7]

        filler_total = (filler_price_per_100g / 100) * filler_grams
        work_price = yarn_length * 1.3
        total = yarn_cost + transport + filler_total + extras + printing + packaging + work_price

        await update.message.reply_text(
            f"Розрахунок завершено:\n"
            f"- Пряжа: {yarn_cost:.2f} грн\n"
            f"- Транспорт: {transport:.2f} грн\n"
            f"- Наповнювач: {filler_total:.2f} грн\n"
            f"- Додаткове: {extras:.2f} грн\n"
            f"- Друк: {printing:.2f} грн\n"
            f"- Пакування: {packaging:.2f} грн\n"
            f"- Робота (довжина х1.3): {work_price:.2f} грн\n"
            f"**Загалом: {total:.2f} грн**"
        )

        users.pop(user_id)

# Запуск Telegram-бота
if __name__ == '__main__':
    TOKEN = os.getenv('TELEGRAM_TOKEN')  # Або встав сюди напряму: 'your_bot_token_here'
    if not TOKEN:
        raise Exception("TELEGRAM_TOKEN не встановлено!")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern="start_calculation"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))

    print("Бот запущено...")
    app.run_polling()
