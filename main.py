import telebot
import sqlite3

BotAPI = '7238767447:AAEaRtQH0PHJdA5XxzUBOx2aqFY0WmlKyMM'

bot = telebot.TeleBot(BotAPI)
databaseName = 'pinboard.sql'

databaseConnection = sqlite3.connect(databaseName)
databaseCursor = databaseConnection.cursor()

databaseCursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INT PRIMARY KEY, 
                        name TEXT, 
                        pinBotBonuses INT
                       )''')
databaseConnection.commit()
databaseCursor.close()
databaseConnection.close()


# Handle newcommers
@bot.message_handler(commands=["start"])
def firstTimeNoFlamePls(message):
    username = getUserInfo(message.from_user.id)
    if username != 0:
        bot.send_message(message.chat.id, f"Привет, а я тебя знаю! Ты {username}")
    else:
        registerNewUser(message)
        username = getUserInfo(message.from_user.id)
        if username == 0:
            bot.send_message(message.chat.id, "Не удалось зарегистрировать нового пользователя")
        else:
            bot.send_message(message.chat.id, f"Привет, {username}, будем знакомы!")

def getUserInfo(telegramID):
    databaseConnection = sqlite3.connect(databaseName)
    databaseCursor = databaseConnection.cursor()

    databaseCursor.execute("SELECT name FROM users WHERE id = ?", (telegramID,))
    result = databaseCursor.fetchall()

    databaseCursor.close()
    databaseConnection.close()

    if not len(result):
        return 0
    else:
        return result[0][0]
    
def registerNewUser(message):
    databaseConnection = sqlite3.connect(databaseName)
    databaseCursor = databaseConnection.cursor()

    databaseCursor.execute("INSERT INTO users (id, name, pinBotBonuses) VALUES(?,?,?)", 
                           (message.from_user.id, message.from_user.first_name, 0,))
    
    databaseConnection.commit()
    databaseCursor.close()
    databaseConnection.close()

    
bot.infinity_polling()