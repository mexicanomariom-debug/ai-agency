from aiogram.fsm.state import State, StatesGroup


class TranslatorStates(StatesGroup):
    waiting_text = State()
