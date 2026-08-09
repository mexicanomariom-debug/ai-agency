from aiogram.fsm.state import State, StatesGroup


class TrafficSetupStates(StatesGroup):
    waiting_origin = State()
    waiting_destination = State()
    waiting_provider = State()
