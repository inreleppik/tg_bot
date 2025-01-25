from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
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
        "/set_profile - Ввод данных профиля\n"
        "/joke - Получить случайную шутку"
    )


# FSM: диалог с пользователем
@router.message(Command("set_profile"))
async def start_sp(message: Message, state: FSMContext):
    gender_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    gender_keyboard.add(KeyboardButton("Мужчина"), KeyboardButton("Женщина"))

    await message.reply("Выберите ваш пол:", reply_markup=gender_keyboard)
    await state.set_state(Form.gender)

@router.message(Form.gender)
async def process_gender(message: Message, state: FSMContext):
    gender = message.text
    if gender not in ["Мужчина", "Женщина"]:
        await message.reply("Пожалуйста, выберите пол из предложенных вариантов.")
        return

    await state.update_data(gender=gender)
    await message.reply("Введите ваш вес (в кг):", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Отмена")))
    await state.set_state(Form.weight)

@router.message(Form.weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        weight = int(message.text)
        await state.update_data(weight=weight)
        await message.reply("Введите ваш рост (в см):")
        await state.set_state(Form.height)
    except ValueError:
        await message.reply("Пожалуйста, введите корректное значение веса.")

@router.message(Form.height)
async def process_height(message: Message, state: FSMContext):
    try:
        height = int(message.text)
        await state.update_data(height=height)
        await message.reply("Введите ваш возраст:")
        await state.set_state(Form.age)
    except ValueError:
        await message.reply("Пожалуйста, введите корректное значение роста.")

@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        await state.update_data(age=age)
        await message.reply("Сколько минут активности у вас в день?")
        await state.set_state(Form.a_time)
    except ValueError:
        await message.reply("Пожалуйста, введите корректное значение возраста.")

@router.message(Form.a_time)
async def process_a_time(message: Message, state: FSMContext):
    try:
        a_time = int(message.text)
        await state.update_data(a_time=a_time)
        await message.reply("В каком городе вы находитесь?")
        await state.set_state(Form.city)
    except ValueError:
        await message.reply("Пожалуйста, введите корректное значение времени активности.")

@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    data = await state.get_data()

    try:
        weight = int(data.get("weight"))
        height = int(data.get("height"))
        age = int(data.get("age"))
        a_time = int(data.get("a_time"))
        city = data.get("city")
        gender = data.get("gender")
    except ValueError:
        await message.reply("Некорректные данные. Пожалуйста, начните заново.")
        await state.clear()
        return

    params = {
        "q": city,
        "appid": W_TOKEN,
        "units": "metric",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(WB_URL, params=params) as response:
            if response.status == 200:
                w = await response.json()
                w = float(w["main"]["temp"])
            else:
                await message.reply("Не удалось получить данные о погоде. Проверьте название города.")
                await state.clear()
                return

    if w >= 30:
        water = weight * 30 + 1000
    elif w >= 25:
        water = weight * 30 + 500
    else:
        water = weight * 30

    # Учитываем пол при расчёте калорий
    if gender == "Мужчина":
        calories = weight * 10 + 6.25 * height - 5 * age + 5
    else:
        calories = weight * 10 + 6.25 * height - 5 * age - 161

    calories *= 1.2  # Коэффициент активности (например, 1.2 для низкой)

    await state.update_data(water_goal=water, calories_goal=calories)

    await message.reply(
        f"Ваши данные:\n"
        f"Пол: {gender}\n"
        f"Вес: {weight} кг\n"
        f"Рост: {height} см\n"
        f"Возраст: {age} лет\n"
        f"Время активности: {a_time} минут\n"
        f"Город: {city}\n"
        f"Норма потребления воды: {water} мл\n"
        f"Норма калорий: {calories} ккал."
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