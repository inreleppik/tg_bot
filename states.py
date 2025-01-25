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
    water_goal = State()
    calories_goal = State()
    logged_water = State()
    logged_calories = State()
    burned_calories = State()
    