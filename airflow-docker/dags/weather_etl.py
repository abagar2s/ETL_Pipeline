from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging  # Add the import for logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    handlers=[
        logging.FileHandler("pipeline.log"),  # Output to a log file
        logging.StreamHandler()  # Output to the console
    ]
)

# Example log
logging.info("Logging setup complete!")

# OpenWeatherMap API configuration
API_KEY = 'c1cb2d3577d444498b1e328a15ed5716'  # Replace with your OpenWeatherMap API key
BASE_URL_WEATHER = "https://api.openweathermap.org/data/2.5/weather"
BASE_URL_AIR_POLLUTION = "https://api.openweathermap.org/data/2.5/air_pollution"
CITY = "New York"  # Replace with your desired city
UNITS = "metric"  # Use "imperial" for Fahrenheit

# PostgreSQL configuration
POSTGRES_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'database': 'airflow',
    'user': 'airflow',
    'password': 'airflow'
}

# Function to create the database if it doesn't exist
def create_database_if_not_exists(config):
    try:
        connection = psycopg2.connect(
            dbname='postgres',
            user=config['user'],
            password=config['password'],
            host=config['host'],
            port=config['port']
        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{config['database']}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {config['database']}")
    except Exception as e:
        raise Exception(f"Error creating database: {e}")
    finally:
        if connection:
            connection.close()

# Function to fetch weather data
def fetch_weather_data():
    logging.info("Fetching weather data...")
    params = {'q': CITY, 'appid': API_KEY, 'units': UNITS}
    try:
        response = requests.get(BASE_URL_WEATHER, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()
        logging.info("Weather data fetched successfully.")
        return {
            'city': CITY,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'weather_condition': data['weather'][0]['main'],
            'weather_description': data['weather'][0]['description']
        }
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching weather data: {e}")
        raise

# Function to fetch air pollution data
def fetch_air_pollution_data(lat, lon):
    logging.info("Fetching air pollution data...")
    params = {'lat': lat, 'lon': lon, 'appid': API_KEY}
    try:
        response = requests.get(BASE_URL_AIR_POLLUTION, params=params)
        response.raise_for_status()
        data = response.json()
        logging.info("Air pollution data fetched successfully.")
        return {
            'aqi': data['list'][0]['main']['aqi'],
            'co': data['list'][0]['components']['co'],
            'no2': data['list'][0]['components']['no2'],
            'o3': data['list'][0]['components']['o3'],
            'pm2_5': data['list'][0]['components']['pm2_5']
        }
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching air pollution data: {e}")
        raise

# Function to store weather data in PostgreSQL
def store_weather_data(**context):
    logging.info("Storing weather data in PostgreSQL...")
    create_database_if_not_exists(POSTGRES_CONFIG)
    data = context['task_instance'].xcom_pull(task_ids='fetch_weather_data')

    if not data:
        logging.error("No weather data available to store.")
        raise ValueError("No weather data available to store.")

    try:
        connection = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = connection.cursor()
        logging.info("Connected to PostgreSQL database.")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather (
            id SERIAL PRIMARY KEY,
            city TEXT,
            date TIMESTAMP,
            temperature REAL,
            feels_like REAL,
            humidity REAL,
            pressure REAL,
            weather_condition TEXT,
            weather_description TEXT
        )
        ''')
        logging.info("Weather table checked/created.")
        cursor.execute('''
        INSERT INTO weather (
            city, date, temperature, feels_like, humidity, pressure,
            weather_condition, weather_description
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data['city'], data['date'], data['temperature'], data['feels_like'], data['humidity'],
            data['pressure'], data['weather_condition'], data['weather_description']
        ))
        connection.commit()
        logging.info("Weather data inserted successfully.")
    except Exception as e:
        logging.error(f"Error storing weather data: {e}")
        raise
    finally:
        if connection:
            connection.close()
            logging.info("Database connection closed.")


# Function to store air pollution data in PostgreSQL
def store_air_pollution_data(**context):
    create_database_if_not_exists(POSTGRES_CONFIG)
    air_data = context['task_instance'].xcom_pull(task_ids='fetch_air_pollution_data')
    if not air_data:
        raise ValueError("No air pollution data available to store.")

    try:
        connection = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS air_pollution (
            id SERIAL PRIMARY KEY,
            aqi INTEGER,
            co REAL,
            no2 REAL,
            o3 REAL,
            pm2_5 REAL
        )
        ''')
        cursor.execute('''
        INSERT INTO air_pollution (
            aqi, co, no2, o3, pm2_5
        )
        VALUES (%s, %s, %s, %s, %s)
        ''', (
            air_data['aqi'], air_data['co'], air_data['no2'], air_data['o3'], air_data['pm2_5']
        ))
        connection.commit()
    except Exception as e:
        raise Exception(f"Error storing air pollution data: {e}")
    finally:
        if connection:
            connection.close()

# Default arguments for DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['your_email@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define DAG
with DAG(
    'weather_air_pollution_pipeline',
    default_args=default_args,
    description='Fetch and store weather and air pollution data in separate tables',
    schedule_interval='@hourly',
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    fetch_weather_data_task = PythonOperator(
        task_id='fetch_weather_data',
        python_callable=fetch_weather_data
    )

    fetch_air_pollution_data_task = PythonOperator(
        task_id='fetch_air_pollution_data',
        python_callable=fetch_air_pollution_data,
        op_kwargs={'lat': 40.7128, 'lon': -74.0060}  # Coordinates for New York
    )

    store_weather_data_task = PythonOperator(
        task_id='store_weather_data',
        python_callable=store_weather_data,
        provide_context=True
    )

    store_air_pollution_data_task = PythonOperator(
        task_id='store_air_pollution_data',
        python_callable=store_air_pollution_data,
        provide_context=True
    )

    fetch_weather_data_task >> store_weather_data_task
    fetch_air_pollution_data_task >> store_air_pollution_data_task

