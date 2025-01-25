from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form
from config import W_TOKEN, WB_URL, T_TOKEN, CN_TOKEN
import aiohttp
import asyncio

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

async def translate_yandex(api_key: str, text: str, source_language: str = "ru", target_language: str = "en"):
    """
    Асинхронная функция для перевода текста с использованием Yandex Translator API.
    
    :param api_key: Ваш API-ключ Yandex Translator.
    :param text: Текст для перевода.
    :param source_language: Исходный язык текста (по умолчанию "ru").
    :param target_language: Целевой язык текста (по умолчанию "en").
    :return: Переведённый текст или сообщение об ошибке.
    """
    url = "https://translate.api.cloud.yandex.net/translate/v2/translate"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {api_key}"
    }

    data = {
        "targetLanguageCode": target_language,
        "texts": [text],
        "sourceLanguageCode": source_language
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                return result["translations"][0]["text"]
            else:
                error = await response.text()
                return f"Ошибка: {response.status}, {error}"
            

async def get_calories_data_async(product_name: str, api_key: str):
    """
    Асинхронный запрос к Calorieninjas API для получения данных о калорийности продукта.
    """
    url = "https://api.calorieninjas.com/v1/nutrition"
    headers = {"X-Api-Key": api_key}
    params = {"query": product_name}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("items", [])
            else:
                return None
            
def get_activity_c(level: str):
    coefs = {"1-2": 1.2,
             "3-4": 1.375,
             "5-6": 1.55,
             "7-8": 1.725,
             "9-10": 1.9}
    return coefs.get(level, 0)

def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:

    if gender == 'Мужской':
        return 10 * weight + 6.25 * height - 5 * age + 5
    elif gender == 'Женский':
        return 10 * weight + 6.25 * height - 5 * age - 161
    else:
        raise ValueError("Некорректный пол. Используйте 'Мужской' или 'Женский'.")

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
        "/log_water\n"
        "/log_food\n"
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
    await message.reply("Выберите соответствующий свой уровень активности из следующих: \n"
                        "1-2: сидячий образ жизни \n"
                        "3-4: легкая физ. нагружка 1-3 раза в неделю \n"
                        "5-6: умеренные тренировки 3-5 раз в неделю \n"
                        "7-8: интенсивные тренировки 6-7 раз в неделю \n"
                        "9-10: тяжелая физ. нагрузка или проф. спорт")
    await message.reply(text = "Выберите свой уровень:",
                        reply_markup=make_column_keyboard(["1-2", "3-4", "5-6", "7-8", "9-10"]))
    await state.set_state(Form.activity)

@router.message(Form.activity)
async def process_activity(message: Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await message.reply("В каком городе вы находитесь?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.city)

@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    data = await state.get_data()

    try:
        gender = str(data.get("gender"))
        weight = int(data.get("weight"))
        height = int(data.get("height"))
        age = int(data.get("age"))
        activity = str(data.get("activity"))
        city = data.get("city")
    except ValueError:
        await message.reply("Некорректные данные. Пожалуйста, начните заново.")
        await state.clear()
        return

    params = {
        "q": await translate_yandex(T_TOKEN, city),
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
                return

    if w >= 30:
        water = weight * 30 + 1000
    elif w >= 25:
        water = weight * 30 + 500
    else:
        water = weight * 30

    calories = calculate_bmr(weight, height, age, gender)  
    calories *= get_activity_c(activity)  

    await state.update_data(water_goal=water, calories_goal=calories)
    await state.update_data(logged_water = 0, logged_calories = 0, burned_calories = 0)

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

@router.message(Command("log_water"))
async def start_lw(message: Message, state: FSMContext):
    await message.reply("Введите выпитое вами количество воды в мл:")
    await state.set_state(Form.logged_water)

@router.message(Form.logged_water)
async def process_lw(message: Message, state: FSMContext):
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        initial_state = float(data.get("logged_water", 0))  # По умолчанию 0
        water_goal = float(data.get("water_goal", 2000))    # Установим 2000 мл по умолчанию
        
        # Проверяем ввод пользователя
        new_water = float(message.text)
        if new_water <= 0:
            await message.reply("Введите положительное число.")
            return

        # Обновляем текущую выпитую воду
        current_state = initial_state + new_water
        u_g = water_goal - current_state  # Корректный расчёт оставшейся воды

        # Обновляем состояние
        await state.update_data(logged_water=current_state)

        # Формируем ответ
        await message.reply(
            f"Вы только что выпили: {new_water} мл воды.\n"
            f"Всего выпито: {current_state} мл воды.\n"
            f"До цели осталось: {max(u_g, 0)} мл воды."  # Если цель достигнута, выводим 0
        )
    except ValueError:
        await message.reply("Пожалуйста, введите корректное число.")

@router.message(Command("log_food"))
async def start_lf(message: Message, state: FSMContext):
    # Начало процесса: запрашиваем продукт
    await message.reply("Какой продукт вы употребили?")
    await state.set_state(Form.logged_calories)


@router.message(Form.logged_calories)
async def process_logged_calories(message: Message, state: FSMContext):
    try:
        # Достаём данные о текущем шаге
        data = await state.get_data()

        if "step" not in data:
            # Первый шаг: обрабатываем название продукта
            product_name = message.text

            # Переводим название продукта
            product_eng = await translate_yandex(T_TOKEN, product_name)
            if not product_eng:
                await message.reply("Не удалось перевести название продукта. Попробуйте снова.")
                return

            # Получаем данные о продукте из API
            product_data = await get_calories_data_async(product_eng, CN_TOKEN)
            if not product_data or not product_data[0].get("calories"):
                await message.reply("Не удалось найти информацию о продукте. Попробуйте указать его более точно.")
                return

            # Извлекаем калорийность
            calories_per_100g = product_data[0]["calories"]

            # Переходим ко второму шагу, запрашиваем количество граммов
            await state.update_data(step="grams", calories_per_100g=calories_per_100g)
            await message.reply(
                f"Продукт: {product_name}\n"
                f"Калорийность: {calories_per_100g} ккал на 100 г.\n"
                "Сколько граммов вы съели?"
            )
        else:
            # Второй шаг: ввод количества граммов
            grams = float(message.text)
            if grams <= 0:
                await message.reply("Введите положительное значение граммов.")
                return

            # Расчёт калорий на основе полученных данных
            calories_per_100g = data["calories_per_100g"]
            total_calories = (calories_per_100g * grams) / 100

            # Сохраняем итоговые калории в logged_calories
            logged_calories = float(data.get("logged_calories", 0)) + total_calories
            await state.update_data(logged_calories=logged_calories)

            # Отправляем итоговый результат
            await message.reply(
                f"Вы съели: {grams:.2f} г.\n"
                f"Калорийность: {total_calories:.2f} ккал.\n"
                f"Общее количество потребленных калорий: {logged_calories:.2f} ккал."
            )

            # Завершаем процесс
            await state.clear()

    except ValueError:
        await message.reply("Введите корректное значение для количества граммов.")
    except Exception as e:
        await message.reply("Произошла ошибка. Попробуйте снова.")
        print(f"Ошибка: {e}")



# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)