from aiogram.fsm.state import State, StatesGroup


class TaskEditStates(StatesGroup):
    waiting_changes = State()
