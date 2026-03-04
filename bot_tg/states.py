from aiogram.fsm.state import State, StatesGroup


class ShopStates(StatesGroup):
    CHOOSING = State()
    HANDLE_MENU = State()
    HANDLE_DESCRIPTION = State()
    HANDLE_CART = State()
    WAITING_EMAIL = State()
    ANSWERING = State()
