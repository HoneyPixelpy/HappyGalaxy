from aiogram.fsm.state import StatesGroup, State    

class DialogStates(StatesGroup):
    waiting_text_prompt = State()
    waiting_image_prompt = State()
