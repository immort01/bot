from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import os

# ✅ Correct way to get your bot token from the environment
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Global store for timetable
timetable = []

scheduler = BackgroundScheduler()
scheduler.start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me your timetable in format:\nHH:MM - Task description")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        time_str, task = text.split(' - ', 1)
        task_time = datetime.datetime.strptime(time_str.strip(), "%H:%M")

        now = datetime.datetime.now()
        schedule_time = now.replace(hour=task_time.hour, minute=task_time.minute, second=0, microsecond=0)

        if schedule_time < now:
            schedule_time += datetime.timedelta(days=1)  # Schedule for tomorrow

        user_id = update.message.chat_id

        scheduler.add_job(
            send_task,
            trigger='date',
            run_date=schedule_time,
            args=[context, user_id, task]
        )

        timetable.append((schedule_time, task))
        await update.message.reply_text(f"Task scheduled: {task} at {schedule_time.strftime('%H:%M')}")

    except Exception:
        await update.message.reply_text("Format should be: HH:MM - Task description")

async def send_task(context, user_id, task):
    await context.bot.send_message(chat_id=user_id, text=f"Reminder: {task}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    app.run_polling()
