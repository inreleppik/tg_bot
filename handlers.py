from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form
from config import W_TOKEN, WB_URL
import aiohttp


router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот.\nВведите /help для списка команд.")

# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/set_profile - \n"
        "/keyboard - Пример кнопок\n"
        "/joke - Получить случайную шутку"
    )

# Обработчик команды /keyboard с инлайн-кнопками
@router.message(Command("keyboard"))
async def show_keyboard(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Кнопка 1", callback_data="btn1")],
            [InlineKeyboardButton(text="Кнопка 2", callback_data="btn2")],
        ]
    )
    await message.reply("Выберите опцию:", reply_markup=keyboard)

@router.callback_query()
async def handle_callback(callback_query):
    if callback_query.data == "btn1":
        await callback_query.message.reply("Вы нажали Кнопка 1")
    elif callback_query.data == "btn2":
        await callback_query.message.reply("Вы нажали Кнопка 2")

# FSM: диалог с пользователем
@router.message(Command("set_profile"))
async def start_sp(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(Form.weight)

@router.message(Form.weight)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(Form.height)

@router.message(Form.height)
async def process_height(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    await message.reply("Введите ваш возраст:")
    await state.set_state(Form.age)

@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.reply("Сколько минут активности у вас в день?")
    await state.set_state(Form.a_time)

@router.message(Form.a_time)
async def process_a_time(message: Message, state: FSMContext):
    await state.update_data(a_time=message.text)
    await message.reply("В каком городе вы находитесь?")
    await state.set_state(Form.city)

@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    data = await state.get_data()
    weight = data.get("weight")
    height = data.get("height")
    age = data.get("age")
    a_time = data.get("a_time")
    city = data.get("city")
    params = {"q": city,
              "appid": W_TOKEN,
              "units": "metric",}
    async with aiohttp.ClientSession() as session:
        async with session.get(WB_URL, params=params) as response:
            if response.status == 200:
                w = await response.json()
                w = w["main"]["temp"]
            else:
                w = None
    if w >= 25:
        water = weight * 30 + 500
    elif w >= 30:
        water = weight * 30 + 1000
    else:
        water = weight * 30

    await state.update_data(water_goal = water)
    calories = weight * 10 + 6.25 * height - 5 * age
    await state.update_data(calories_goal = calories)
    await message.reply("Ваши данные:\n"
                        f"Вес - {weight} кг \n"
                        f"Рост - {height} см \n"
                        f"Возраст - {age} лет \n"
                        f"Время активности - {a_time} Город - {city} \n"
                        f"Норма потребления воды - {water} мл \n"
                        f"Норма калорий - {calories}"
                        )
    await state.clear()

# Получение шутки из API
@router.message(Command("joke"))
async def get_joke(message: Message):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.chucknorris.io/jokes/random") as response:
            joke = await response.json()
            await message.reply(joke["value"])

# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)