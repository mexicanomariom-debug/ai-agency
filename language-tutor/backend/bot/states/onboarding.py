from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    choosing_audience = State()
    choosing_language = State()
    choosing_level = State()
    placement_test = State()
    chatting = State()
