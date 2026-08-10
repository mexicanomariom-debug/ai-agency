from aiogram.fsm.state import State, StatesGroup


class ReconSetupStates(StatesGroup):
    waiting_url = State()
    waiting_interest = State()
    waiting_verify = State()
    waiting_keywords = State()
