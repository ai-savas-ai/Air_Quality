from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import os
from model_training import run_forecast


API_KEY = "enter your openweathermap api key"

app = FastAPI()

# Настройка шаблонов и статики
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_city_coordinates(city):
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]['lat'], data[0]['lon']
    return None


def get_weather_data(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


def get_air_pollution(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['list'][0]
    return None


def classify_air_quality(aqi):
    return {
        1: "Хорошее",
        2: "Умеренное",
        3: "Вредное для чувствительных групп",
        4: "Вредное",
        5: "Опасное"
    }.get(aqi, "Unknown")


@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    default_city = "Rostov-na-Donu"
    context = {"request": request, "city": default_city}

    coordinates = get_city_coordinates(default_city)
    if not coordinates:
        context["error"] = f"City '{default_city}' not found."
        return templates.TemplateResponse("index.html", context)

    lat, lon = coordinates
    weather_data = get_weather_data(lat, lon)
    pollution_data = get_air_pollution(lat, lon)

    if weather_data:
        context["temp"] = weather_data['main']['temp']
        context["description"] = weather_data['weather'][0]['description'].title()
        icon_code = weather_data['weather'][0]['icon']
        context["icon_url"] = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"

    if pollution_data:
        aqi = pollution_data['main']['aqi']
        context["aqi"] = aqi
        context["aqi_class"] = classify_air_quality(aqi)
        context["pollutants"] = pollution_data['components']

    forecast_df = run_forecast()
    context["forecast_html"] = forecast_df.to_html(classes="forecast-table", border=0)

    return templates.TemplateResponse("index.html", context)


@app.post("/", response_class=HTMLResponse)
async def form_post(request: Request, city: str = Form(...)):
    context = {"request": request, "city": city}

    coordinates = get_city_coordinates(city)
    if not coordinates:
        context["error"] = f"City '{city}' not found."
        return templates.TemplateResponse("index.html", context)

    lat, lon = coordinates
    weather_data = get_weather_data(lat, lon)
    pollution_data = get_air_pollution(lat, lon)

    if weather_data:
        context["temp"] = weather_data['main']['temp']
        context["description"] = weather_data['weather'][0]['description'].title()
        icon_code = weather_data['weather'][0]['icon']
        context["icon_url"] = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"

    if pollution_data:
        aqi = pollution_data['main']['aqi']
        context["aqi"] = aqi
        context["aqi_class"] = classify_air_quality(aqi)
        context["pollutants"] = pollution_data['components']

    forecast_df = run_forecast()
    context["forecast_html"] = forecast_df.to_html(classes="forecast-table", border=0)

    return templates.TemplateResponse("index.html", context)