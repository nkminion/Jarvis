import requests
from datetime import datetime

def time_to_tts(time_str):
    parts = list(map(int, time_str.split(":")))
    hour, minute = parts[0], parts[1]
    
    am_pm = "in the morning" if hour < 12 else "in the evening"
    if hour >= 12:
        hour -= 12
    if hour == 0:
        hour = 12
    
    # Format minute and second part
    minute_part = f"{minute}" if minute else "o'clock"
    
    return f"{hour} {minute_part} {am_pm}"

from datetime import datetime

def date_to_tts(date_str):
    dt = datetime.fromisoformat(date_str)
    
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    def ordinal(n):
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"
    
    month_name = months[dt.month - 1]
    
    return f"{month_name} {ordinal(dt.day)}, {dt.year}"



def get_weather_forecast(location, date, time):
    # 1. Convert location to latitude/longitude
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}"
    geo_data = requests.get(geo_url).json()
    
    if "results" not in geo_data:
        return "Location not found."
    
    lat = geo_data["results"][0]["latitude"]
    lon = geo_data["results"][0]["longitude"]
    place = geo_data["results"][0]["name"]
    
    # 2. Fetch weather forecast
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,weathercode"
        f"&timezone=auto"
    )
    weather_data = requests.get(weather_url).json()
    
    # 3. Find the closest hour to the given date & time
    target_dt = datetime.fromisoformat(f"{date}T{time}")
    times = [datetime.fromisoformat(t) for t in weather_data["hourly"]["time"]]
    
    closest_idx = min(range(len(times)), key=lambda i: abs(times[i] - target_dt))
    
    temp = weather_data["hourly"]["temperature_2m"][closest_idx]
    rain = weather_data["hourly"]["precipitation"][closest_idx]
    code = weather_data["hourly"]["weathercode"][closest_idx]
    
    weather_desc = WEATHER_CODES.get(code, "Unknown")

    # TTS-friendly string
    tts = (
        f"Here's the weather forecast for {location} on {date_to_tts(date)} at {time_to_tts(time)}. "
        f"The temperature is {temp:.1f} degrees Celsius. "
        f"Precipitation is {rain:.1f} millimeters. "
        f"In short, {weather_desc}."
    )
    
    return tts

# Mapping of weather codes to descriptions
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

# Example usage:
# print(get_weather_forecast("Bangalore", "2025-10-11", "15:00"))
