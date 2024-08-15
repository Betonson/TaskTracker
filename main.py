import telebot
import sqlite3
import time
from datetime import datetime
from threading import Thread

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

TIMEINPUT = range(1)
PIN_HEADER_INPUT, PIN_DESC_INPUT, PIN_DUEDATE_INPUT, PIN_SETALARM_INPUT = range(4)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

database_Pinboard = 'pinboard.sql'

# Handle newcommers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = get_user_info(update.effective_message.from_user.id)
    if username != 0:
        await context.bot.send_message(update.effective_message.chat.id, f"Привет, а я тебя знаю! Ты {username}")
    else:
        register_new_user(update.effective_message)
        username = get_user_info(update.effective_message.from_user.id)
        if username == 0:
            await context.bot.send_message(update.effective_message.chat.id, "Не удалось зарегистрировать нового пользователя, сорян")
        else:
            await context.bot.send_message(update.effective_message.chat.id, f"Привет, {username}, будем знакомы!")

async def init_timer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"На какое время установить таймер?")
    return TIMEINPUT
        

# async def setTimerInThread(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     timeFromMessage = datetime.strptime(update.effective_message.text,'%H:%M') 
#     totalMinutes = timeFromMessage.minute - time.localtime().tm_min if timeFromMessage.minute > time.localtime().tm_min else 60 + timeFromMessage.minute - time.localtime().tm_min
#     total_seconds = (timeFromMessage.hour-time.localtime().tm_hour)*3600 + (totalMinutes)*60 - time.localtime().tm_sec
#     await context.bot.send_message(update.effective_message.chat.id, f"Устанавливаю таймер на {update.effective_message.text}")
#     await context.bot.send_message(update.effective_message.chat.id, f"Таймер сработает через {total_seconds} секунд")
#     timerThread = Thread(target=sleepStarter, args=(update.effective_message.chat.id, total_seconds,))
#     timerThread.start()

async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    await context.bot.send_message(job.chat_id, text=f"Сработал таймер Сейчас {time.localtime()}")

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

async def set_timer_in_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_message.chat_id
    timeFromMessage = datetime.strptime(update.effective_message.text,'%H:%M')
    totalMinutes = timeFromMessage.minute - time.localtime().tm_min if timeFromMessage.minute > time.localtime().tm_min else 60 + timeFromMessage.minute - time.localtime().tm_min
    total_seconds = (timeFromMessage.hour-time.localtime().tm_hour)*3600 + (totalMinutes)*60 - time.localtime().tm_sec

    job_removed = remove_job_if_exists(str(chat_id)+update.effective_message.text, context)
    context.job_queue.run_once(alarm, total_seconds, chat_id=chat_id, name=str(chat_id)+update.effective_message.text, data=total_seconds)

    await context.bot.send_message(update.effective_message.chat.id, f"Устанавливаю таймер на {update.effective_message.text}")
    await context.bot.send_message(update.effective_message.chat.id, f"Таймер сработает через {total_seconds} секунд")



# def sleepStarter(chatID,total_seconds):
#     time.sleep(total_seconds)
#     context.bot.send_message(chatID, f"Сработал таймер Сейчас {time.localtime()}")

def get_user_info(telegramID):
    databaseConnection = sqlite3.connect(database_Pinboard)
    databaseCursor = databaseConnection.cursor()

    databaseCursor.execute("SELECT name FROM users WHERE id = ?", (telegramID,))
    result = databaseCursor.fetchall()

    databaseCursor.close()
    databaseConnection.close()

    if not len(result):
        return 0
    else:
        return result[0][0]
    
def register_new_user(message):
    databaseConnection = sqlite3.connect(database_Pinboard)
    databaseCursor = databaseConnection.cursor()

    databaseCursor.execute("INSERT INTO users (id, name, pinBotBonuses) VALUES(?,?,?)", 
                           (message.from_user.id, message.from_user.first_name, 0,))
    
    databaseConnection.commit()
    databaseCursor.close()
    databaseConnection.close()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day."
    )

    return ConversationHandler.END
    
def main() -> None:
    BotAPI = '7238767447:AAEaRtQH0PHJdA5XxzUBOx2aqFY0WmlKyMM'

    initialise_basic_tables()

    application = Application.builder().token(BotAPI).build()
    application.add_handler(CommandHandler(["start"], start))

    timer_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("settimer", init_timer_handler)],
        states={
            TIMEINPUT: [MessageHandler(filters.Regex("[0-2][0-9]:[0-5][0-9]"), set_timer_in_job)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(timer_conv_handler)

    new_pin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("newpin", create_new_pin)],
        states={
            PIN_HEADER_INPUT:   [MessageHandler(filters.Regex("[0-2][0-9]:[0-5][0-9]"), set_timer_in_job)],
            PIN_DESC_INPUT:     [MessageHandler(filters.Regex("[0-2][0-9]:[0-5][0-9]"), set_timer_in_job), CommandHandler("skip", skip_desc)],
            PIN_DUEDATE_INPUT:  [MessageHandler(filters.Regex("[0-2][0-9]:[0-5][0-9]"), set_timer_in_job), CommandHandler("skip", skip_duedate)],
            PIN_SETALARM_INPUT: [MessageHandler(filters.Regex("[0-2][0-9]:[0-5][0-9]"), set_timer_in_job), CommandHandler("skip", skip_setalarm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(new_pin_conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

def initialise_basic_tables():
    databaseConnection = sqlite3.connect(database_Pinboard)
    databaseCursor = databaseConnection.cursor()

    # Initialise USERS table
    databaseCursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY, 
                            name TEXT, 
                            pinBotBonuses INT
                        )''')
    databaseConnection.commit()

    # initialise Pinboard table
    databaseCursor.execute('''CREATE TABLE IF NOT EXISTS pinboard (
                            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
                            creation_date TEXT NOT NULL,
                            user_id TEXT NOT NULL, 
                            due_date TEXT,
                            header TEXT,
                            description TEXT,
                            remind NUMERIC,
                            pinBotBonusesValue INT
                        )''')
    databaseConnection.commit()

    databaseCursor.close()
    databaseConnection.close()

if __name__ == "__main__":
    main()