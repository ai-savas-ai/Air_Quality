import time
import requests
from datetime import datetime, timedelta
import os
import logging
import csv  # Новый импорт для работы с CSV

# Конфигурация
API_KEY = "enter your openweathermap api key"
LAT = 47.222531
LON = 39.718705
CSV_FILE = "air_quality_history.csv"  # Теперь CSV
LOG_FILE = "air_quality_log.log"
LAST_TIME_FILE = "last_time.txt"

# Настройка логирования
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_current_air_pollution(lat, lon, api_key):
    url = "http://api.openweathermap.org/data/2.5/air_pollution"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка запроса: {e}")
        print(f"Ошибка запроса: {e}")
        return None

def initialize_csv():
    """
    Создаёт CSV-файл с заголовками, если он не существует.
    """
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Date", "Time", "AQI", "PM10", "PM2.5", "NO2", "SO2", "CO", "O3"
            ])
        logging.info(f"Создан новый CSV-файл: {CSV_FILE}")
        print(f"Создан новый CSV-файл: {CSV_FILE}")

def load_last_time():
    if os.path.exists(LAST_TIME_FILE):
        with open(LAST_TIME_FILE, 'r') as f:
            timestamp = f.read().strip()
            if timestamp:
                return int(timestamp)
    return None

def save_last_time(timestamp):
    with open(LAST_TIME_FILE, 'w') as f:
        f.write(str(timestamp))

def save_to_csv(entry):
    dt_unix = entry["dt"]
    dt_utc = datetime.utcfromtimestamp(dt_unix)
    dt_msk = dt_utc + timedelta(hours=3)  # Москва UTC+3

    date_str = dt_msk.strftime("%Y-%m-%d")
    time_str = dt_msk.strftime("%H:%M:%S")

    aqi = entry["main"]["aqi"]
    comps = entry["components"]

    # Функция для безопасного приведения к int
    def to_int(value):
        try:
            return int(round(float(value)))  # Округляем при необходимости
        except (TypeError, ValueError):
            return 0  # или None, если предпочитаешь пустые ячейки

    row_data = [
        date_str,
        time_str,
        to_int(aqi),
        to_int(comps.get("pm10")),
        to_int(comps.get("pm2_5")),
        to_int(comps.get("no2")),
        to_int(comps.get("so2")),
        to_int(comps.get("co")),
        to_int(comps.get("o3")),
    ]

    existing = False
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Пропуск заголовков
            for row in reader:
                if len(row) < 2:
                    continue
                existing_date, existing_time = row[0], row[1]
                if existing_date == date_str and existing_time.startswith(time_str[:2]):
                    existing = True
                    break

    if not existing:
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row_data)
        logging.info(f"Сохранено: {date_str} {time_str} MSK")
        print(f"Сохранено: {date_str} {time_str} MSK")
    else:
        logging.info(f"Запись за {date_str} {time_str[:2]}:00 MSK уже существует. Пропуск.")
        print(f"Запись за {date_str} {time_str[:2]}:00 MSK уже существует. Пропуск.")

def fetch_and_save():
    data = get_current_air_pollution(LAT, LON, API_KEY)
    if data is None:
        print("Не удалось получить данные о качестве воздуха.")
        logging.warning("Не удалось получить данные о качестве воздуха.")
        return False

    measurements = data.get("list", [])
    if not measurements:
        print("Нет измерений в полученных данных.")
        logging.warning("Нет измерений в полученных данных.")
        return False

    entry = measurements[0]
    save_to_csv(entry)
    save_last_time(entry["dt"])
    return True

def wait_until_next_hour():
    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    sleep_seconds = (next_hour - now).total_seconds()
    logging.info(f"Ждём до следующего часа: {next_hour.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Ждём до следующего часа: {next_hour.strftime('%Y-%m-%d %H:%M:%S')}")
    time.sleep(sleep_seconds)

def main():
    print("Скрипт сбора данных о качестве воздуха запущен.")
    logging.info("Скрипт сбора данных о качестве воздуха запущен.")

    initialize_csv()

    while True:
        success = False
        for attempt in range(1, 6):  # Пять попыток
            print(f"Попытка {attempt} сбора данных...")
            logging.info(f"Попытка {attempt} сбора данных...")
            success = fetch_and_save()
            if success:
                print("Данные успешно собраны и сохранены.")
                logging.info("Данные успешно собраны и сохранены.")
                break
            else:
                if attempt < 5:
                    print(f"Попытка {attempt} не удалась. Повтор через 1 минуту.")
                    logging.warning(f"Попытка {attempt} не удалась. Повтор через 1 минуту.")
                    time.sleep(60)
                else:
                    print("Не удалось собрать данные после 5 попыток.")
                    logging.error("Не удалось собрать данные после 5 попыток.")

        wait_until_next_hour()

if __name__ == "__main__":
    main()