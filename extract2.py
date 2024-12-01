import requests
import sqlite3
from datetime import datetime

# OpenWeatherMap API configuration
API_KEY = 'my api key'  # Replace with your OpenWeatherMap API key
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
CITY = "New York"  # Replace with your desired city
UNITS = "metric"  # Use "imperial" for Fahrenheit

# Step 1: Fetch Weather Data from the API
def fetch_weather_data(city):
    params = {
        'q': city,
        'appid': API_KEY,
        'units': UNITS
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        return {
            'city': city,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': data['main']['temp'],
            'feels_like': data['main']['feels_like'],  # Perceived temperature
            'temp_min': data['main']['temp_min'],  # Minimum temperature
            'temp_max': data['main']['temp_max'],  # Maximum temperature
            'humidity': data['main']['humidity'],  # Humidity percentage
            'pressure': data['main']['pressure'],  # Atmospheric pressure in hPa
            'weather_condition': data['weather'][0]['main'],  # General weather condition
            'weather_description': data['weather'][0]['description'],  # Detailed weather description
            'icon': data['weather'][0]['icon'],  # Icon code for weather condition
            'visibility': data.get('visibility', 'N/A'),  # Visibility in meters (if available)
            'wind_speed': data['wind']['speed'],  # Wind speed
            'wind_direction': data['wind'].get('deg', 'N/A'),  # Wind direction in degrees
            'cloud_coverage': data['clouds'].get('all', 'N/A'),  # Cloud coverage percentage
            'sunrise': datetime.utcfromtimestamp(data['sys']['sunrise']).strftime('%H:%M:%S'),  # Sunrise time (UTC)
            'sunset': datetime.utcfromtimestamp(data['sys']['sunset']).strftime('%H:%M:%S'),  # Sunset time (UTC)
            'country': data['sys']['country']  # Country code
        }
    else:
        print(f"Error: Unable to fetch data for {city}. Status Code: {response.status_code}")
        return None

# Step 2: Store Data in SQLite Database
def store_weather_data(data):
    """
    Stores weather data into a SQLite database.

    Args:
    - data (dict): A dictionary containing weather data.
    """
    # Connect to SQLite database
    connection = sqlite3.connect('weather_data.db')
    cursor = connection.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weather (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT,
        date TEXT,
        temperature REAL,
        feels_like REAL,
        temp_min REAL,
        temp_max REAL,
        humidity REAL,
        pressure REAL,
        weather_condition TEXT,
        weather_description TEXT,
        icon TEXT,
        visibility REAL,
        wind_speed REAL,
        wind_direction REAL,
        cloud_coverage REAL,
        sunrise TEXT,
        sunset TEXT,
        country TEXT
    )
    ''')

    # Insert weather data
    cursor.execute('''
    INSERT INTO weather (
        city, date, temperature, feels_like, temp_min, temp_max,
        humidity, pressure, weather_condition, weather_description, icon,
        visibility, wind_speed, wind_direction, cloud_coverage, sunrise, sunset, country
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['city'], data['date'], data['temperature'], data['feels_like'], data['temp_min'], 
        data['temp_max'], data['humidity'], data['pressure'], data['weather_condition'], 
        data['weather_description'], data['icon'], data['visibility'], data['wind_speed'], 
        data['wind_direction'], data['cloud_coverage'], data['sunrise'], data['sunset'], 
        data['country']
    ))

    # Commit and close the connection
    connection.commit()
    connection.close()
    print(f"Data for {data['city']} stored successfully.")

# Step 3: Automate the Task
if __name__ == "__main__":
    weather_data = fetch_weather_data(CITY)
    if weather_data:
        store_weather_data(weather_data)
