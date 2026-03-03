from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_products_keyboard(products):
    """Принимает список товаров из Strapi (поле 'data').
    Возвращает Inline-клавиатуру с кнопками для каждого товара.
    """
    buttons = []

    for product in products:
        product_id = product["documentId"]
        title = product["title"]

        btn = InlineKeyboardButton(text=title, callback_data=str(product_id))
        buttons.append([btn])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_keyboard():
    """Возвращает клавиатуру с одной кнопкой 'Назад'."""
    keyboard = [[InlineKeyboardButton(text="Назад к списку", callback_data="back")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
