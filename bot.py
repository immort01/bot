from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import os

# Get token securely from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")


# Global store for timetable
timetable = []

scheduler = BackgroundScheduler()
scheduler.start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me your timetable in format:\nHH:MM - Task description")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lines = text.strip().split('\n')
    successful = []

    for line in lines:
        try:
            time_str, task = line.split(' - ', 1)
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
            successful.append(f"{schedule_time.strftime('%H:%M')} - {task}")

        except Exception:
            continue  # skip invalid lines silently for now

    if successful:
        await update.message.reply_text("Scheduled:\n" + "\n".join(successful))
    else:
        await update.message.reply_text("Please use format: HH:MM - Task description (one per line)")

async def send_task(context, user_id, task):
    await context.bot.send_message(chat_id=user_id, text=f"Reminder: {task}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    app.run_polling()
