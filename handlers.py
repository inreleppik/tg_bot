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

def make_column_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    """
    Создаёт реплай-клавиатуру с кнопками, расположенными в две колонки
    :param items: список текстов для кнопок
    :return: объект реплай-клавиатуры
    """
    # Разделяем список на строки по 2 элемента
    rows = [items[i:i+2] for i in range(0, len(items), 2)]
    # Создаём кнопки и группируем их по строкам
    keyboard = [[KeyboardButton(text=item) for item in row] for row in rows]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

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
    t = """Выберите соответствующий свой уровень активности из следующих:\n
    "1-2: сидячий образ жизни \n3-4: легкая физ. нагружка 1-3 раза в неделю \n
    5-6: умеренные тренировки 3-5 раз в неделю \n7-8: интенсивные тренировки 6-7 раз в неделю \n
    9-10: тяжелая физ. нагрузка или проф. спорт"""
    await message.reply(text = t, reply_markup=make_column_keyboard(["1-2", "3-4", "5-6", "7-8", "9-10"]))
    await state.set_state(Form.activity)

@router.message(Form.a_time)
async def process_a_time(message: Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await message.reply("В каком городе вы находитесь?", reply_markup=ReplyKeyboardRemove())
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
        activity = data.get("activity")
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
        f"Уровень активности: {activity}\n"
        f"Город: {city}\n"
        f"Норма потребления воды: {water} мл\n"
        f"Норма калорий: {calories} ккал."
    )
    await state.clear()



# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)