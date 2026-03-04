from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard(products):
    """Главное меню: кнопки товаров + кнопка корзины."""
    buttons = []

    buttons.append(
        [InlineKeyboardButton(text="🛒 Моя корзина", callback_data="show_cart")]
    )

    for product in products:
        product_id = product["documentId"]
        title = product["title"]

        buttons.append(
            [InlineKeyboardButton(text=title, callback_data=str(product_id))]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_product_detail_keyboard():
    """Клавиатура под карточкой товара: Добавить, Корзина, Назад."""
    keyboard = [
        [InlineKeyboardButton(text="Добавить в корзину", callback_data="add_to_cart")],
        [InlineKeyboardButton(text="🛒 Моя корзина", callback_data="show_cart")],
        [InlineKeyboardButton(text="Назад к списку товаров", callback_data="back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cart_keyboard(items):
    """Клавиатура для корзины: удаление, оплата, назад.."""
    buttons = []

    for item in items:
        item_id = item["item_id"]

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"❌ Удалить {item.get('title', '')[:20]}",
                    callback_data=f"delete_{item_id}",
                )
            ]
        )
    buttons.append([InlineKeyboardButton(text="Оплатить", callback_data="checkout")])

    buttons.append(
        [InlineKeyboardButton(text="Назад к списку товаров", callback_data="back")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_menu_keyboard():
    """Клавиатура с кнопкой возврата в меню."""
    keyboard = [
        [InlineKeyboardButton(text="Назад к списку товаров", callback_data="back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
