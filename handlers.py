from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form
from config import W_TOKEN, WB_URL, T_TOKEN, CN_TOKEN
import aiohttp


users = {} 

def get_user_storage(user_id: int) -> dict:
    if user_id not in users:
        users[user_id] = {
            "gender": None,
            "weight": 0,
            "height": 0,
            "age": 0,
            "activity": "1-2",
            "city": "",
            "water_goal": 2000,
            "calorie_goal": 2000,
            "logged_water": 0,
            "logged_calories": 0,
            "burned_calories": 0
        }
    return users[user_id]

def make_row_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    row = [KeyboardButton(text=item) for item in items]
    return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)

def make_column_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    rows = [items[i:i+2] for i in range(0, len(items), 2)]
    keyboard = [[KeyboardButton(text=item) for item in row] for row in rows]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

async def translate_yandex(api_key: str, text: str, source_language: str = "ru", target_language: str = "en"):
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

def calculate_calories(weight, activity, duration_minutes):
    MET = {
        "Бег": 9.8,
        "Ходьба": 3.8,
        "Велоспорт": 8.0,
        "Плавание": 6.0,
        "Йога": 2.5,
        "Кардио": 7.0,
        "Танцы": 5.5,
        "Силовая": 6.0,
    }
    calories_per_minute = MET.get(activity, 0) * 3.5 * weight / 200
    return calories_per_minute * duration_minutes

def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    if gender == 'Мужской':
        return 10 * weight + 6.25 * height - 5 * age + 5
    elif gender == 'Женский':
        return 10 * weight + 6.25 * height - 5 * age - 161
    else:
        raise ValueError("Некорректный пол. Используйте 'Мужской' или 'Женский'.")

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот.\nВведите /help для списка команд.")

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/set_profile - Настройка профиля\n"
        "/log_water - Учёт выпитой воды\n"
        "/log_food - Учёт потреблённых калорий\n"
        "/log_workout - Учёт потраченных калорий\n"
    )

@router.message(Command("set_profile"))
async def start_sp(message: Message, state: FSMContext):
    await message.reply(
        text="Выберите ваш пол:",
        reply_markup=make_row_keyboard(['Мужской', 'Женский'])
    )
    await state.set_state(Form.gender)

@router.message(Form.gender)
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.reply("Введите ваш вес (в кг):", reply_markup=ReplyKeyboardRemove())
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
    await message.reply(
        "Выберите соответствующий уровень активности:\n"
        "1-2: сидячий образ жизни\n"
        "3-4: лёгкая нагрузка 1-3 раза/нед\n"
        "5-6: умеренные тренировки 3-5 раз/нед\n"
        "7-8: интенсивные тренировки 6-7 раз/нед\n"
        "9-10: тяжёлая физ. нагрузка или проф. спорт\n",
        reply_markup=make_column_keyboard(["1-2", "3-4", "5-6", "7-8", "9-10"])
    )
    await state.set_state(Form.activity)

@router.message(Form.activity)
async def process_activity(message: Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await message.reply("В каком городе вы находитесь?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.city)

@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city = message.text)
    data = await state.get_data()
    user_id = message.from_user.id
    
    try:
        gender = str(data.get("gender"))
        weight = int(data.get("weight"))
        height = int(data.get("height"))
        age = int(data.get("age"))
        activity = str(data.get("activity"))
        city = data.get("city")
    except ValueError:
        await message.reply("Некорректные данные. Пожалуйста, начните заново /set_profile.")
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
                resp_json = await response.json()
                temperature = float(resp_json["main"]["temp"])
            else:
                await message.reply("Не удалось получить данные о погоде. Проверьте название города.")
                await state.clear()
                return

    if temperature >= 30:
        water_goal = weight * 30 + 1000
    elif temperature >= 25:
        water_goal = weight * 30 + 500
    else:
        water_goal = weight * 30

    calories = calculate_bmr(weight, height, age, gender)
    calories *= get_activity_c(activity)
    user_data = get_user_storage(user_id)
    user_data["gender"] = gender
    user_data["weight"] = weight
    user_data["height"] = height
    user_data["age"] = age
    user_data["activity"] = activity
    user_data["city"] = city
    user_data["water_goal"] = water_goal
    user_data["calorie_goal"] = calories
    user_data["logged_water"] = 0
    user_data["logged_calories"] = 0
    user_data["burned_calories"] = 0

    await message.reply(
        f"Ваши данные:\n"
        f"Пол: {gender}\n"
        f"Вес: {weight} кг\n"
        f"Рост: {height} см\n"
        f"Возраст: {age} лет\n"
        f"Уровень активности: {activity}\n"
        f"Город: {city}\n"
        f"Норма воды: {water_goal} мл\n"
        f"Норма калорий: {calories:.2f} ккал.\n\n"
        "Профиль сохранён!"
    )
    await state.clear()

@router.message(Command("log_water"))
async def start_lw(message: Message, state: FSMContext):
    await message.reply("Введите выпитое вами количество воды в мл:")
    await state.set_state(Form.logged_water)

@router.message(Form.logged_water)
async def process_lw(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        user_data = get_user_storage(user_id)
        initial_water = float(user_data.get("logged_water", 0))
        water_goal = float(user_data.get("water_goal", 2000))
        
        new_water = float(message.text)
        if new_water <= 0:
            await message.reply("Введите положительное число.")
            return

        current_water = initial_water + new_water
        user_data["logged_water"] = current_water 
        
        remainder = water_goal - current_water
        if remainder < 0:
            remainder = 0
        
        await message.reply(
            f"Вы выпили: {new_water} мл.\n"
            f"Всего сегодня: {current_water} мл.\n"
            f"Осталось до цели: {remainder} мл."
        )
        await state.clear()
    except ValueError:
        await message.reply("Пожалуйста, введите корректное число.")

@router.message(Command("log_food"))
async def start_lf(message: Message, state: FSMContext):
    await message.reply("Какой продукт вы употребили?")
    await state.set_state(Form.logged_calories)

@router.message(Form.logged_calories)
async def process_logged_calories(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    
    try:
        if "step" not in data:
            product_name = message.text
            
            product_eng = await translate_yandex(T_TOKEN, product_name)
            if not product_eng:
                await message.reply("Не удалось перевести название продукта. Попробуйте снова.")
                return
            
            product_data = await get_calories_data_async(product_eng, CN_TOKEN)
            if not product_data or not product_data[0].get("calories"):
                await message.reply("Не нашёл информацию о продукте. Уточните название.")
                return

            calories_per_100g = product_data[0]["calories"]
            
            await state.update_data(step="grams", calories_per_100g=calories_per_100g)
            await message.reply(
                f"Продукт: {product_name}\n"
                f"Ккал на 100 г: {calories_per_100g}\n"
                f"Сколько граммов вы съели?"
            )
        else:
            grams = float(message.text)
            if grams <= 0:
                await message.reply("Введите положительное число граммов.")
                return

            calories_per_100g = data["calories_per_100g"]
            total_calories = (calories_per_100g * grams) / 100

            user_data = get_user_storage(user_id)
            old_cals = float(user_data.get("logged_calories", 0))
            user_data["logged_calories"] = old_cals + total_calories

            await message.reply(
                f"Съедено: {grams} г.\n"
                f"Калорийность: {total_calories:.2f} ккал.\n"
                f"Всего за сегодня: {user_data['logged_calories']:.2f} ккал."
            )
            await state.clear()
    except ValueError:
        await message.reply("Введите корректное число граммов.")
    except Exception as e:
        await message.reply("Произошла ошибка. Попробуйте снова.")
        print(f"Ошибка: {e}")

@router.message(Command("log_workout"))
async def start_lwo(message: Message, state: FSMContext):
    await message.reply(
        "Какой вид тренировки вы выполняли?\n"
        "(Выберите наиболее подходящий среди следующих)",
        reply_markup=make_column_keyboard(['Бег', 'Ходьба', 'Велоспорт', 'Плавание',
                                            'Йога', 'Кардио', 'Танцы', 'Силовая'])
    )
    await state.set_state(Form.burned_calories) 

@router.message(Form.burned_calories)
async def process_wo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()

    try:

        if "step" not in data:
            wo_name = message.text

            await state.update_data(step = "workout", wo_name = wo_name)
            await message.reply("Введите количество времени в минутах, которое вы потратили на свою тренировку:",
                                reply_markup=ReplyKeyboardRemove())
            
        else:
            minutes = int(message.text)
            if minutes <= 0:
                await message.reply("Введите положительное число минут.")
                return
            wo_name = data['wo_name']
            user_data = get_user_storage(user_id)
            weight = int(user_data.get("weight", 0))
            intial_state_w = float(user_data.get("water_goal", 0))
            intial_state_cb = float(user_data.get("burned_calories", 0))
            burned_calories = int(calculate_calories(weight, wo_name, minutes))
            additional_water = int(6.67 * minutes)
            user_data["burned_calories"] = intial_state_cb + burned_calories
            user_data["water_goal"] = intial_state_w + additional_water 

            await message.reply(f"{wo_name} {minutes} минут - {burned_calories} ккал. \n"
                                f"Дополнительно: выпейте {additional_water} мл воды.")
            
            await state.clear()

    except ValueError:
        await message.reply("Введите корректное число минут.")
    except Exception as e:
        await message.reply("Произошла ошибка. Попробуйте снова.")
        print(f"Ошибка: {e}")

@router.message(Command("check_progress"))
async def cmd_cp(message: Message):
    user_id = message.from_user.id
    user_data = get_user_storage(user_id)
    logged_water = int(user_data.get("logged_water", 0))
    logged_calories = int(user_data.get("logged_calories", 0))
    burned_calories = int(user_data.get("burned_calories", 0))
    water_goal = int(user_data.get("water_goal", 0))
    calories_goal = int(user_data.get("calorie_goal", 0))
    water_to_drink = water_goal - logged_water
    calories_balance = logged_calories - burned_calories

    await message.reply("Прогресс: \n"
                        "Вода: \n"
                        f"- Выпито: {logged_water} мл из {calories_goal} мл. \n"
                        f"- Осталось: {water_to_drink} мл. \n \n"
                        "Калории: \n"
                        f"- Потреблено: {logged_calories} ккал из {calories_goal} ккал. \n"
                        f"- Сожжено: {burned_calories} ккал. \n"
                        f"- Баланс: {calories_balance} ккал.")


def setup_handlers(dp):
    dp.include_router(router)