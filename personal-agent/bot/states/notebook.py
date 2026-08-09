from aiogram.fsm.state import State, StatesGroup


class NotebookStates(StatesGroup):
    writing = State()
