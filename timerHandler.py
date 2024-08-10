import time
from datetime import datetime
import telebot
from threading import Thread

class TimerHandler:
    def __init__(self, secondCount, botObject, message) -> None:
        self.secondCount = secondCount
        self.bot = botObject
        self.message = message

    def askForInput(self,):
        self.bot.send_message(self.message.chat.id, f"Устанавливаю таймер на {self.secondCount} секунд")
        self.bot.register_next_step_handler(self.message, self.setTimerInThread)
        

    def setTimerInThread(self,message):
        timeFromMessage = datetime.strptime(message.text,'%H:%M') 
        totalMinutes = timeFromMessage.minute - time.localtime().tm_min if timeFromMessage.minute > time.localtime().tm_min else 60 + timeFromMessage.minute - time.localtime().tm_min
        total_seconds = (totalMinutes)*60 + (timeFromMessage.hour-time.localtime().tm_hour)*3600
        self.bot.send_message(self.message.chat.id, f"Устанавливаю таймер на {message.text}")
        # timerThread = Thread(target=self.sleepStarter, args=(secondCount,))
        self.bot.send_message(self.message.chat.id, f"Таймер сработает через {total_seconds} секунд")


    def sleepStarter(self,secondCount):
        time.sleep(secondCount)
        self.bot.send_message(self.message.chat.id, f"Сработал таймерю Сейчас {time.localtime()}")
        
        
    