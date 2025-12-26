from aiogram.fsm.state import State, StatesGroup


class DialogStates(StatesGroup):
    waiting_text_prompt = State()
    waiting_image_prompt = State()
