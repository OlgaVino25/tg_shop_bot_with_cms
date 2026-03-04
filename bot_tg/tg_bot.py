import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

from settings import TG_TOKEN, ADMIN_CHAT_ID
from bot_tg import handlers as tg_h
from bot_tg.states import ShopStates
from logger import setup_logging




logger = logging.getLogger(__name__)


async def main():
    setup_logging(
        telegram_token=TG_TOKEN, admin_chat_id=ADMIN_CHAT_ID, logger_instance=None
    )

    bot = Bot(token=TG_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.register(tg_h.start, Command(commands=["start"]))
    dp.callback_query.register(tg_h.add_to_cart_handler, F.data == "add_to_cart")
    dp.callback_query.register(tg_h.show_cart_handler, F.data == "show_cart")
    dp.callback_query.register(tg_h.checkout_handler, F.data == "checkout")
    dp.callback_query.register(tg_h.back_to_products, F.data == "back")
    dp.callback_query.register(
        tg_h.delete_from_cart_handler, F.data.startswith("delete_")
    )
    dp.callback_query.register(tg_h.process_product_selection, F.data != "back")
    dp.message.register(tg_h.process_email_input, ShopStates.WAITING_EMAIL)
    dp.message.register(tg_h.handle_unknown)
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("Непредвиденная ошибка в Telegram боте")
        raise


if __name__ == "__main__":
    asyncio.run(main())
