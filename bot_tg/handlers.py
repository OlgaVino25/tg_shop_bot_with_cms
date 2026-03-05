import logging

from aiogram import types
from aiogram.types import BufferedInputFile
from aiogram.fsm.context import FSMContext
from requests.exceptions import RequestException

from bot_tg.states import ShopStates
from bot_tg.keyboards import (
    get_main_menu_keyboard,
    get_product_detail_keyboard,
    get_back_to_menu_keyboard,
    get_cart_keyboard,
)
from bot_tg.strapi_client import (
    fetch_products,
    fetch_product,
    fetch_product_image,
    get_or_create_cart,
    add_to_cart,
    get_cart_contents,
    delete_cart_item,
    create_customer,
)


logger = logging.getLogger(__name__)


def format_cart_text(items):
    """Форматирует текст корзины из списка товаров."""
    if not items:
        return "🛒 Ваша корзина пуста."
    text = "🛒 *Ваша корзина:*\n\n"
    total = 0.0
    for item in items:
        title = item.get("title", "?")
        price = item.get("price", 0)
        qty = item.get("quantity", 0)
        cost = price * qty
        text += f"• {title} — {qty} кг × {price} руб. = {cost:.2f} руб.\n"
        total += cost
    text += f"\n*Итого: {total:.2f} руб.*"
    return text


async def send_products_list(chat_id, bot, state):
    """Общая логика получения товаров и отправки клавиатуры."""
    try:
        products = fetch_products()
    except RequestException:
        logger.exception("Ошибка при запросе товаров")
        await bot.send_message(chat_id, "Не удалось подключиться к базе товаров.")
        return

    if not products:
        await bot.send_message(chat_id, "Товаров пока нет.")
        return

    keyboard = get_main_menu_keyboard(products)
    await bot.send_message(chat_id, "Наши товары:", reply_markup=keyboard)
    await state.set_state(ShopStates.HANDLE_MENU)


async def start(message: types.Message, state: FSMContext):
    await send_products_list(message.chat.id, message.bot, state)


async def process_product_selection(callback: types.CallbackQuery, state: FSMContext):
    """Показывает детальную информацию о выбранном товаре."""
    product_id = callback.data
    await state.update_data(current_product_id=product_id)
    try:
        product = fetch_product(product_id)
    except RequestException:
        logger.exception("Ошибка при запросе товара")
        await callback.answer("Ошибка загрузки товара.", show_alert=True)
        return

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
    state_data = await state.get_data()
    product_id = state_data.get("current_product_id")
    if not product_id:
        await callback.answer("Ошибка: товар не найден.")
        return

    try:
        cart_id = get_or_create_cart(user_id)
    except RequestException:
        logger.exception("Ошибка при получении/создании корзины")
        await callback.answer("Не удалось создать корзину.", show_alert=True)
        return

    try:
        add_to_cart(cart_id, product_id, quantity=1.0)
    except RequestException:
        logger.exception("Ошибка при добавлении товара в корзину")
        await callback.answer("❌ Ошибка при добавлении.", show_alert=True)
        return

    await callback.answer("✅ Товар добавлен в корзину!", show_alert=True)


async def show_cart_handler(callback: types.CallbackQuery, state: FSMContext):
    """Показывает содержимое корзины пользователя."""
    user_id = str(callback.from_user.id)

    try:
        cart_id = get_or_create_cart(user_id)
    except RequestException:
        logger.exception("Ошибка при получении корзины.", show_alert=True)
        await callback.answer("Не удалось получить корзину.", show_alert=True)
        return

    try:
        items = get_cart_contents(cart_id)
    except RequestException:
        logger.exception("Ошибка при получении содержимого корзины")
        await callback.message.answer("Не удалось загрузить корзину.")
        await callback.answer()
        return

    text = format_cart_text(items)

    await callback.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_cart_keyboard(items) if items else get_back_to_menu_keyboard(),
    )

    await state.set_state(ShopStates.HANDLE_CART)
    await callback.answer()


async def delete_from_cart_handler(callback: types.CallbackQuery, state: FSMContext):
    """Удаляет выбранный товар из корзины и обновляет сообщение."""
    item_id = callback.data.split("_", 1)[1]

    try:
        delete_cart_item(item_id)
    except RequestException:
        logger.exception("Ошибка при удалении товара из корзины.")
        await callback.message.edit_text("Ошибка при удалении товара.")
        return

    await callback.answer("Товар удалён из корзины.")

    user_id = str(callback.from_user.id)

    try:
        cart_id = get_or_create_cart(user_id)
        items = get_cart_contents(cart_id)
    except RequestException:
        logger.exception("Ошибка при обновлении корзины после удаления")
        await callback.message.edit_text("Не удалось обновить корзину.")
        return

    if not items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста.",
            reply_markup=get_back_to_menu_keyboard(),
        )
        await state.set_state(ShopStates.HANDLE_CART)
        return

    text = format_cart_text(items)
    await callback.message.edit_text(
        text, parse_mode="Markdown", reply_markup=get_cart_keyboard(items)
    )
    await state.set_state(ShopStates.HANDLE_CART)


async def checkout_handler(callback: types.CallbackQuery, state: FSMContext):
    """Запрашивает email для связи и переводит в состояние WAITING_EMAIL."""
    await callback.message.answer(
        "Для оформления заказа укажите вашу электронную почту.\n"
        "Наш менеджер свяжется с вами для подтверждения."
    )

    await state.set_state(ShopStates.WAITING_EMAIL)
    await callback.answer()


async def process_email_input(message: types.Message, state: FSMContext):
    """Получает email, выводит его в консоль и возвращает пользователя в меню."""
    email = message.text.strip()

    if "@" not in email or "." not in email:
        await message.answer(
            "Пожалуйста, введите корректный email (например, name@domain.com)."
        )
        return

    user_id = str(message.from_user.id)

    try:
        customer_id = create_customer(user_id, email)
    except RequestException:
        logger.exception("Ошибка при создании клиента")
        await message.answer("Не удалось сохранить ваши данные. Попробуйте позже.")
        return

    logger.info(f"Customer saved with ID {customer_id}")
    await message.answer(
        f"Спасибо! Ваш email {email} принят. Мы скоро свяжемся с вами."
    )

    await send_products_list(message.chat.id, message.bot, state)


async def handle_unknown(message: types.Message, state: FSMContext):
    """Обработчик для нераспознанных сообщений."""
    await message.answer("Перевожу на оператора")
