import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# Чтение токена из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")

W_TOKEN = os.getenv("WEATHER_TOKEN")

if not W_TOKEN:
    raise ValueError("Переменная окружения WEATHER_TOKEN не установлена!")

T_TOKEN = os.getenv("TRANSLATOR_TOKEN")

if not T_TOKEN:
    raise ValueError("Переменная окружения TRANSLATOR_TOKEN не установлена!")

CN_TOKEN = os.getenv("CALORIES_TOKEN")

if not CN_TOKEN:
    raise ValueError("Переменная окружения CALORIES_TOKEN не установлена!")

WB_URL = "http://api.openweathermap.org/data/2.5/weather"