import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from sklearn.linear_model import LinearRegression
from streamlit.runtime.uploaded_file_manager import UploadedFile

from util.mappings import city_to_country


@st.cache_data
def load_data(file: UploadedFile) -> pd.DataFrame:
    return pd.read_csv(file)


@st.cache_data
def get_current_temp(city, token):
    country = city_to_country[city]
    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={token}&units=metric")
    if response.status_code != 200:
        st.error(response.json())
        return None
    return response.json()['main']['temp']


@st.cache_data
def check_api_token(token):
    if get_current_temp("London", token) is None:
        return False
    st.success("API ключ валидный!")
    st.snow()
    return True


@st.cache_data
def get_temp_data(city, data):
    city_data = data[data['city'] == city]
    season_profile = city_data.groupby('season')['temperature'].agg(['mean', 'std'])
    city_data['mean_temp'] = city_data['season'].map(season_profile['mean'])
    city_data['std_temp'] = city_data['season'].map(season_profile['std'])
    anomalies = city_data[
        abs(city_data['temperature'] - city_data['mean_temp']) > 2 * city_data['std_temp']
        ]
    min_temp = city_data['temperature'].min()
    max_temp = city_data['temperature'].max()
    avg_temp = city_data['temperature'].mean()

    trend = calculate_trend(city_data)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=city_data['timestamp'],
        y=city_data['temperature'],
        mode='markers',
        name=f"{city} Температура",
        marker=dict(size=8, color='blue', opacity=0.7)
    ))

    fig.add_trace(go.Scatter(
        x=city_data['timestamp'],
        y=trend,
        mode='lines',
        name=f"{city} Линия тренда",
        line=dict(color='red', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=anomalies['timestamp'],
        y=anomalies['temperature'],
        mode='markers',
        name="Аномалии",
        marker=dict(size=10, color='orange', symbol='x', opacity=1)
    ))

    fig.update_layout(
        title=f"Температурный тренд для города {city} (легенда кликабельна)",
        xaxis_title="Дата",
        yaxis_title="Температура, °C",
        legend=dict(orientation="h", x=0.5, xanchor="center", y=1.1, yanchor="top"),
        template="plotly_white"
    )

    return season_profile, anomalies, min_temp, max_temp, avg_temp, fig


@st.cache_data
def calculate_trend(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['days_since_start'] = (df['timestamp'] - df['timestamp'].min()).dt.days

    X = df[['days_since_start']]
    y = df['temperature']

    lin_reg = LinearRegression()
    lin_reg.fit(X, y)

    return lin_reg.predict(X)
