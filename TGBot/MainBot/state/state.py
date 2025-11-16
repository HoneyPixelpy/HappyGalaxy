from aiogram.fsm.state import StatesGroup, State    

class Auth_state(StatesGroup):
    No = State() # Для блокировки действий юзера.
    Start_query = State() # После стартовой пересылки сообщений.
    why_are_you = State() # Определяемся кто мы
    Gender = State() # Определяем пол
    Age = State() # Определяем возраст
    FIO = State() # Определяем ФИО
    Success_FIO = State()
    nickname = State() # Определяем псевдоним
    phone = State() # Определяем телефон
    final = State() # Подтверждаем
    success_ruls = State() # Подтверждаем

class RegPersonal(StatesGroup):
    Gender = State() # Определяем пол
    Age = State() # Определяем возраст
    FIO = State() # Определяем ФИО
    Success_FIO = State()
    phone = State() # Определяем телефон
    final = State() # Подтверждаем
    success_ruls = State() # Подтверждаем

class FindUser(StatesGroup):
    user_id = State()
    send_msg = State()
    change_balance = State()

class Mailing(StatesGroup):
    Pin = State()
    Media = State()
    Text = State()
    Confirm = State()

class CreateBonus(StatesGroup):
    type_bonus = State()
    size_starcoins = State()
    max_quantity = State()
    click_scale = State()
    expires_at_hours = State()

class Offer(StatesGroup):
    shop = State()

class VKProfile(StatesGroup):
    url = State()

class Idea(StatesGroup):
    wait = State()

class Daily(StatesGroup):
    wait = State()

class Msg_Delete(StatesGroup):
    Activate = State()

class SPromocodes(StatesGroup):
    wait = State()

class SInteractiveGame(StatesGroup):
    wait_data = State()
