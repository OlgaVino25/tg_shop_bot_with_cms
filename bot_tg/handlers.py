import sys
import logging

from aiogram import types
from aiogram.types import BufferedInputFile
from aiogram.fsm.context import FSMContext

from bot_tg.states import ShopStates
from bot_tg.keyboards import get_products_keyboard, get_product_detail_keyboard
from bot_tg.strapi_client import (
    fetch_products,
    fetch_product,
    fetch_product_image,
    get_or_create_cart,
    add_to_cart,
)

from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

logger = logging.getLogger(__name__)


async def send_products_list(chat_id, bot, state):
    """Общая логика получения товаров и отправки клавиатуры."""
    products = fetch_products()
    if products is None:
        await bot.send_message(chat_id, "Не удалось подключиться к базе товаров.")
        return False
    if not products:
        await bot.send_message(chat_id, "Товаров пока нет.")
        return False
    keyboard = get_products_keyboard(products)
    await bot.send_message(chat_id, "Наши товары:", reply_markup=keyboard)
    await state.set_state(ShopStates.HANDLE_MENU)
    return


async def start(message: types.Message, state: FSMContext):
    await send_products_list(message.chat.id, message.bot, state)


async def process_product_selection(callback: types.CallbackQuery, state: FSMContext):
    """Показывает детальную информацию о выбранном товаре."""
    product_id = callback.data
    await state.update_data(current_product_id=product_id)
    product = fetch_product(product_id)

    if not product:
        await callback.answer("Товар не найден.")
        return

    await callback.message.delete()

    title = product.get("title", "Без названия")
    description = product.get("description", "Нет описания")
    price = product.get("price", 0)

    text = f"{title}\n\n{description}\n\nЦена: {price} руб."

    image = fetch_product_image(product)

    if image:
        await callback.message.answer_photo(
            photo=BufferedInputFile(image.getvalue(), filename="product.jpg"),
            caption=text,
            reply_markup=get_product_detail_keyboard(),
        )
    else:
        await callback.message.answer(text, reply_markup=get_product_detail_keyboard())

    await state.set_state(ShopStates.HANDLE_DESCRIPTION)
    await callback.answer()


async def back_to_products(callback: types.CallbackQuery, state: FSMContext):
    await send_products_list(callback.message.chat.id, callback.message.bot, state)
    await callback.answer()


async def add_to_cart_handler(callback: types.CallbackQuery, state: FSMContext):
    """Добавляет текущий товар в корзину пользователя."""
    user_id = str(callback.from_user.id)
    data = await state.get_data()
    product_id = data.get("current_product_id")
    if not product_id:
        await callback.answer("Ошибка: товар не найден.")
        return

    cart_id = get_or_create_cart(user_id)
    if not cart_id:
        await callback.answer("Не удалось создать корзину.", show_alert=True)
        return

    success = add_to_cart(cart_id, product_id, quantity=1.0)
    if success:
        await callback.answer("✅ Товар добавлен в корзину!", show_alert=True)
    else:
        await callback.answer("❌ Ошибка при добавлении.", show_alert=True)


async def handle_unknown(message: types.Message, state: FSMContext):
    """Обработчик для нераспознанных сообщений."""
    await message.answer("Перевожу на оператора")
