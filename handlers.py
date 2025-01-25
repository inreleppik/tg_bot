from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form
from config import W_TOKEN, WB_URL
import aiohttp

def make_row_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    """
    Создаёт реплай-клавиатуру с кнопками в один ряд
    :param items: список текстов для кнопок
    :return: объект реплай-клавиатуры
    """
    row = [KeyboardButton(text=item) for item in items]
    return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)

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
        "/set_profile - Настройка профиля\n"
        "/joke - Получить случайную шутку"
    )


# FSM: диалог с пользователем
@router.message(Command("set_profile"))
async def start_sp(message: Message, state: FSMContext):
    await message.reply(text = "Выберите ваш пол:",
                        reply_markup = make_row_keyboard(['Мужской','Женский']))
    await state.set_state(Form.gender)

@router.message(Form.gender)
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender = message.text)
    await message.reply("Введите ваш вес (в кг):", 
                        reply_markup=ReplyKeyboardRemove())
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

    try:
        gender = data.get("gender")
        weight = int(data.get("weight"))
        height = int(data.get("height"))
        age = int(data.get("age"))
        a_time = int(data.get("a_time"))
        city = data.get("city")
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

    calories = weight * 10 + 6.25 * height - 5 * age  # Формула для мужчин
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