from aiogram.fsm.state import State, StatesGroup


class ReconSetupStates(StatesGroup):
    waiting_type = State()
    waiting_url = State()
    waiting_label = State()
