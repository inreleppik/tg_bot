from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    gender = State()
    weight = State()
    height = State()
    age = State()
    level_a = State()
    activity = State()
    type_a = State()
    a_time = State()
    city = State()