from datetime import datetime

import streamlit as st

from util.functions import load_data, get_current_temp, check_api_token, get_temp_data
from util.mappings import month_to_season

st.set_page_config(
    page_title="Start page",
    page_icon="👋",
)

st.markdown(
    """
### Аналитическая платформа для работы с погодными данными 
    """
)

token = st.text_input("Введите API ключ OpenWeatherMap", "")
if token:
    is_correct = check_api_token(token)

uploaded_file = st.file_uploader("Загрузите исторические данные", type=["csv"])

if uploaded_file:
    df = load_data(uploaded_file)
    st.success("Данные успешно загружены!")

    cities = df['city'].unique()
    selected_city = st.selectbox("Выберите город", cities)

    st.write(f"Температура в городе {selected_city}:")
    profile, anomalies, min_temp, max_temp, avg_temp, fig = get_temp_data(selected_city, df)

    st.write(f"Средняя температура: {avg_temp:.2f} °C")
    st.write(f"Минимальная температура: {min_temp:.2f} °C")
    st.write(f"Максимальная температура: {max_temp:.2f} °C")

    st.write("Сезонный профиль:")
    st.dataframe(profile,
                 column_config={'mean': 'mean, °C', 'std': 'std, °C'}
                 )

    print(type(anomalies))
    st.plotly_chart(fig)

    temp_button = st.button("Получить текущую температуру")
    if temp_button:
        temp = get_current_temp(selected_city, token)
        st.snow()

        st.write(f"Температура в городе {selected_city}: {temp} °C")
        season = month_to_season[datetime.now().month]
        if abs(temp - profile.loc[season, 'mean']) > 2 * profile.loc[season, 'std']:
            st.error("Текущая температура аномальна для сезона!")
        else:
            st.success("Текущая температура не аномальна для сезона")
