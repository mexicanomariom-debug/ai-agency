from aiogram.fsm.state import State, StatesGroup


class ReconSetupStates(StatesGroup):
    waiting_url = State()
