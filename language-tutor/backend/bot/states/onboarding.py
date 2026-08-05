from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    choosing_language = State()
    choosing_level = State()
    chatting = State()
    voice_chatting = State()
