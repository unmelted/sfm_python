import os
import logging
from datetime import datetime
from logging.handlers import SocketHandler
import telebot
from logging import Handler, LogRecord

BOT_TOKEN = '5578949849:AAEJHteVLGJnydip3x5eYwJQQgcPymWGu4s'
CHAT_ID = '1140943041'

class TelegramBotHandler(Handler):
    def __init__(self, token: str, chat_id: str):
        super().__init__()
        self.token = token
        self.chat_id = chat_id

    def emit(self, record: LogRecord):
        bot = telebot.TeleBot(self.token)
        bot.send_message(
            self.chat_id,
            self.format(record)
        )

class Logger(object) :
    instance = None

    @staticmethod
    def get() :
        if Logger.instance is None:
            Logger.instance = Logger(['file', 'viewer', 'console', 'bot'])
            # Logger.instance = Logger(['file', 'console', 'bot'])            
        return Logger.instance

    def __init__ (self, type, ip='127.0.0.1') :
        print("logger init is called")
        self.w = logging.getLogger(__name__)
        formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')            
        log_dir = os.path.join(os.getcwd(), 'log')
        if not os.path.exists(log_dir) :
            os.makedirs(log_dir)       

        if 'file' in type:
            print("called? 1")
            now = datetime.now()
            logname = os.path.join( log_dir, datetime.strftime(now, '%Y%m%d') + 'Calib.txt')            
            file_handler = logging.FileHandler(logname)
            file_handler.setLevel(logging.INFO)            
            file_handler.setFormatter(formatter)
            self.w.addHandler(file_handler)

        if 'console' in type  :
            print("called? 2")
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console.setFormatter(formatter)
            self.w.addHandler(console)


        if 'viewer' in type:            
            socket_handler = SocketHandler(ip, 19996)  # default listening address
            socket_handler.setLevel(logging.INFO)                        
            socket_handler.setFormatter(formatter)
            self.w.addHandler(socket_handler)

        if 'bot' in type:
            print("called? 3")            
            # telegram_log_handler = TelegramLoggingHandler(BOT_TOKEN, CHANNEL_NAME)
            telegram_log_handler = TelegramBotHandler(BOT_TOKEN, CHAT_ID)
            formatter = logging.Formatter('%(asctime)s : %(name)s : %(message)s')                        
            telegram_log_handler.setLevel(logging.ERROR)            
            self.w.addHandler(telegram_log_handler)
