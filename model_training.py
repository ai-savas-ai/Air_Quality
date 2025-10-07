import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import matplotlib.pyplot as plt
import datetime


def load_and_prepare_data(filename):
    df = pd.read_csv(filename, parse_dates=['Date'])
    df.sort_values('Date', inplace=True)
    df.set_index('Date', inplace=True)

    # Только числовые признаки
    features = ['AQI', 'PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3']
    data = df[features]

    # Масштабирование
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)

    return scaled_data, scaler, df.index[-1]


def create_sequences(data, window_size):
    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i:i + window_size])
        y.append(data[i + window_size])
    return np.array(X), np.array(y)


def build_model(input_shape):
    model = Sequential()
    model.add(LSTM(64, return_sequences=True, input_shape=input_shape))
    model.add(LSTM(32))
    model.add(Dense(7))  # 7 выходов: AQI, PM2.5, ...
    model.compile(optimizer='adam', loss='mse')
    return model


def forecast_future(model, last_sequence, days, scaler):
    predictions = []
    input_seq = last_sequence.copy()

    for _ in range(days):
        pred = model.predict(input_seq[np.newaxis, :, :])[0]
        predictions.append(pred)
        input_seq = np.vstack([input_seq[1:], pred])  # сдвиг окна

    # Обратно к реальным значениям
    return scaler.inverse_transform(predictions)


def main():
    file_path = "air_quality_history.csv"
    window_size = 30
    forecast_days = 7

    data, scaler, last_date = load_and_prepare_data(file_path)
    X, y = create_sequences(data, window_size)

    # Разделить на обучающую и тестовую (например, 90%)
    split = int(len(X) * 0.9)
    X_train, y_train = X[:split], y[:split]

    model = build_model((window_size, X.shape[2]))
    model.fit(X_train, y_train, epochs=50, batch_size=16, verbose=1)

    last_sequence = data[-window_size:]
    future = forecast_future(model, last_sequence, forecast_days, scaler)


    forecast_dates = [last_date + datetime.timedelta(days=i) for i in range(1, forecast_days + 1)]
    forecast_df = pd.DataFrame(future, columns=['AQI', 'PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3'], index=forecast_dates)

    print("📈 Прогноз на 7 дней вперед:")
    print(forecast_df)


    # Построим график AQI
    forecast_df['AQI'].plot(title='Прогноз AQI на 7 дней', marker='o')
    plt.xlabel("Дата")
    plt.ylabel("AQI")
    plt.grid(True)
    plt.show()

def run_forecast():
    file_path = "air_quality_history.csv"
    window_size = 30
    forecast_days = 7

    data, scaler, last_date = load_and_prepare_data(file_path)
    X, y = create_sequences(data, window_size)

    split = int(len(X) * 0.9)
    X_train, y_train = X[:split], y[:split]

    model = build_model((window_size, X.shape[2]))
    model.fit(X_train, y_train, epochs=50, batch_size=16, verbose=0)

    last_sequence = data[-window_size:]
    future = forecast_future(model, last_sequence, forecast_days, scaler)

    forecast_dates = [last_date + datetime.timedelta(days=i) for i in range(1, forecast_days + 1)]
    forecast_df = pd.DataFrame(future, columns=['AQI', 'PM2.5', 'PM10', 'NO2', 'SO2', 'CO', 'O3'], index=forecast_dates)

    return forecast_df