import requests

def get_weather(city, api_key):
    # URL for the weather API
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    # Make a request to the API
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        # Extract relevant information
        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp']
        humidity = data['main']['humidity']

        return (weather_description, temperature, humidity)
    else:
        return ("Error", "Error", "Error")

# Replace with your city and API key
city = "Rajahmundry"  # Change to your desired city
api_key = "2dc0e4e6c6042a8a97042e2cec5040ae"  # Replace with your OpenWeatherMap API key

get_weather(city, api_key)


"""
Weather in Rajahmundry:
Description: overcast clouds
Temperature: 24.98°C
Humidity: 94%
"""