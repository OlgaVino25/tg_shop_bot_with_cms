import logging
import traceback
import requests


logger = logging.getLogger("app_logger")


class TelegramErrorsHandler(logging.Handler):

    def __init__(self, telegram_token, admin_chat_id):
        super().__init__()
        self.telegram_token = telegram_token
        self.admin_chat_id = admin_chat_id

    def emit(self, record):
        if record.levelno < logging.WARNING:
            return

        if not self.telegram_token or not self.admin_chat_id:
            return

        try:
            msg = f"Ошибка в боте\n\n"
            msg += f"Время: {record.asctime}\n"
            msg += f"Уровень: {record.levelname}\n"
            msg += f"Модуль: {record.module}\n"
            msg += f"Сообщение: {record.getMessage()}\n"

            if record.exc_info:
                exc_type, exc_value, exc_tb = record.exc_info
                tb_text = "".join(
                    traceback.format_exception(exc_type, exc_value, exc_tb)
                )

                if len(tb_text) > 1000:
                    tb_text = tb_text[-1000:]
                msg += f"\nТрейсбек:\n{tb_text}"

            self._send_to_telegram(msg)

        except Exception as e:
            print(f"Не удалось отправить лог в Telegram: {e}")

    def _send_to_telegram(self, msg):
        """Синхронная отправка сообщения через Telegram Bot API"""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

        payload = {"chat_id": self.admin_chat_id, "text": msg}
        try:
            response = requests.post(url, json=payload, timeout=10)
            if not response.ok:
                print(f"⚠️ Не удалось отправить сообщение в Telegram: {response.text}")
        except Exception as e:
            print(f"❌ Не удалось отправить сообщение в Telegram: {e}")


def setup_logging(telegram_token=None, admin_chat_id=None, logger_instance=None):
    """Настраивает логирование.

    Args:
        telegram_token: Токен Telegram бота для отправки ошибок. Если None, то Telegram логгер не добавляется.
        admin_chat_id: ID чата для отправки ошибок. Если None, то Telegram логгер не добавляется.
        logger_instance: Логгер для настройки. Если None, настраивается корневой логгер.
    """
    if logger_instance is None:
        logger_instance = logging.getLogger()

    logger_instance.setLevel(logging.DEBUG)
    logger_instance.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(process)d - %(levelname)s - %(pathname)s - %(lineno)d - %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger_instance.addHandler(console_handler)

    if telegram_token and admin_chat_id:
        telegram_handler = TelegramErrorsHandler(telegram_token, admin_chat_id)
        telegram_handler.setLevel(logging.WARNING)
        logger_instance.addHandler(telegram_handler)

    return logger_instance
