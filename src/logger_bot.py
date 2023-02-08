import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions, executor

API_TOKEN = '5578949849:AAEJHteVLGJnydip3x5eYwJQQgcPymWGu4s'


class LoggerBot(object) :

    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.log = logging.getLogger('broadcast')

        self.bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
        self.dp = Dispatcher(self.bot)
        executor.start(self.dp, self.broadcaster())

    def get_users(self):
        """
        Return users list
        In this example returns some random ID's
        """
        yield from (61043901, 78238238, 78378343, 98765431, 12345678)


    async def send_message(self, user_id: int, text: str, disable_notification: bool = False) -> bool:
        """
        Safe messages sender
        :param user_id:
        :param text:
        :param disable_notification:
        :return:
        """
        try:
            await self.bot.send_message(user_id, text, disable_notification=disable_notification)
        except exceptions.BotBlocked:
            self.log.error(f"Target [ID:{user_id}]: blocked by user")
        except exceptions.ChatNotFound:
            self.log.error(f"Target [ID:{user_id}]: invalid user ID")
        except exceptions.RetryAfter as e:
            self.log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
            await asyncio.sleep(e.timeout)
            return await self.send_message(user_id, text)  # Recursive call
        except exceptions.UserDeactivated:
            self.log.error(f"Target [ID:{user_id}]: user is deactivated")
        except exceptions.TelegramAPIError:
            self.log.exception(f"Target [ID:{user_id}]: failed")
        else:
            self.log.info(f"Target [ID:{user_id}]: success")
            return True
        return False


    async def broadcaster(self) -> int:
        """
        Simple broadcaster
        :return: Count of messages
        """
        count = 0
        try:
            # for user_id in self.get_users():
            if await self.send_message('1140943041', '<b>Hello!</b> Start Loggerbot!'):
                count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
        finally:
            self.log.info(f"{count} messages successful sent.")

        return count
