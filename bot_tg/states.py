from aiogram.fsm.state import State, StatesGroup


class ShopStates(StatesGroup):
    CHOOSING = State()
    HANDLE_MENU = State()
    ANSWERING = State()
