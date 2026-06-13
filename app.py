from dotenv import load_dotenv
load_dotenv()

import os
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from groq import Groq

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

weather_cache = {}

@app.get("/", response_class=HTMLResponse)
def read_index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html file not found.")

@app.get("/api/weather-dashboard")
def get_dashboard_data(lat: float, lon: float, name: str):
    if not OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenWeather Key missing in .env file.")
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Groq API Key missing in .env file.")

    cache_key = f"{round(lat, 2)}_{round(lon, 2)}"
    current_time = datetime.utcnow()

    if cache_key in weather_cache:
        cached_entry = weather_cache[cache_key]
        if current_time - cached_entry["timestamp"] < timedelta(minutes=10):
            return cached_entry["data"]

    # Reverse Geocoding
    geo_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={OPENWEATHER_API_KEY}"
    geo_res = requests.get(geo_url)
    geo_data = geo_res.json()
    state_name = geo_data[0].get("state", "") if geo_data else ""
    country_code = geo_data[0].get("country", "") if geo_data else ""

    # Current Weather
    current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
    res = requests.get(current_url)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail="Failed to fetch current weather telemetry.")
    current_data = res.json()

    resolved_city_name = name if name else current_data.get("name", "Unknown Location")

    # 5-Day Forecast
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
    f_res = requests.get(forecast_url)
    forecast_list = f_res.json().get("list", []) if f_res.status_code == 200 else []
    
    future_forecast = []
    for item in forecast_list:
        if "12:00:00" in item["dt_txt"]:
            future_forecast.append({
                "date": item["dt_txt"].split(" ")[0],
                "temp": item["main"]["temp"],
                "description": item["weather"][0]["description"],
                "icon": item["weather"][0]["icon"]
            })

    # 5-Day History
    today = current_time.date()
    archive_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={today - timedelta(days=5)}&end_date={today - timedelta(days=1)}&daily=temperature_2m_max,temperature_2m_min,rain_sum&timezone=auto"
    h_res = requests.get(archive_url)
    h_data = h_res.json().get("daily", {}) if h_res.status_code == 200 else {}
    
    past_history = []
    if h_data:
        for i in range(len(h_data.get("time", []))):
            past_history.append({
                "date": h_data["time"][i],
                "max_temp": h_data["temperature_2m_max"][i],
                "min_temp": h_data["temperature_2m_min"][i],
                "rain": h_data["rain_sum"][i]
            })

    # High-Speed Stable Generation Pipeline
    ai_advice = "### What to Wear\nMetrics incomplete.\n### Precautions\nMetrics incomplete.\n### Activity\nMetrics incomplete."
    
    try:
        temp = current_data['main']['temp']
        humidity = current_data['main']['humidity']
        if humidity > 65 and temp > 30:
            comfort_index = "High Muggy Index / Elevated Heat Fatigue Risk"
        elif humidity > 55:
            comfort_index = "Moderate Humidity Friction / Sticky Conditions"
        else:
            comfort_index = "Pleasant Atmospheric Balance / Low Moisture Strain"

        client = Groq(api_key=GROQ_API_KEY)
        
        prompt_text = f"""
        CONTEXT RULES: You are a specialized AI/ML Weather Intelligence Agent. Parse this climate data and return exact bullet points under the requested headings. Never output introductory small talk or conclusions.

        DATA CONTEXT METRICS FOR {resolved_city_name.upper()}:
        - Air Temperature: {temp}°C
        - Relative Humidity: {humidity}%
        - Real-time Condition: {current_data['weather'][0]['description']}
        - Pre-calculated Comfort Matrix: {comfort_index}
        
        OUTPUT FORMAT SPECIFICATION:
        ### What to Wear
        - [Provide clothing pairing matching the calculated comfort index]
        - [Provide clothing fabric details]

        ### Precautions & Safety
        - [Provide hydration target relative to moisture friction]
        - [Provide safety action for local state conditions]

        ### Activity Recommendation
        - [Provide optimized outdoor option]
        - [Provide climate-controlled indoor option]
        """

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_text}],
            model="llama-3.3-70b-versatile",
            temperature=0.2
        )
        ai_advice = chat_completion.choices[0].message.content
    except Exception as e:
        ai_advice = f"### Error\nGeneration engine error: {str(e)}"

    final_payload = {
        "city_name": resolved_city_name,
        "country": country_code if country_code else current_data.get("sys", {}).get("country", ""),
        "state": state_name,
        "current": {
            "temp": current_data["main"]["temp"],
            "feels_like": current_data["main"]["feels_like"],
            "humidity": current_data["main"]["humidity"],
            "wind_speed": current_data["wind"]["speed"],
            "description": current_data["weather"][0]["description"],
            "icon": current_data["weather"][0]["icon"]
        },
        "forecast": future_forecast[:5],
        "history": past_history,
        "ai_advice": ai_advice
    }

    weather_cache[cache_key] = {
        "timestamp": current_time,
        "data": final_payload
    }

    return final_payload

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)