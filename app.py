import streamlit as st
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from ipywidgets import interact
import ipywidgets as widgets

# Load your CSV file (replace with your file path)
csv_file_path = "/content/drive/MyDrive/banknifty_data09.csv"
data = pd.read_csv(csv_file_path)

# Combine 'date' and 'time' columns into a single 'datetime' column
data['datetime'] = pd.to_datetime(data['date'] + ' ' + data['time'])
data.set_index('datetime', inplace=True)

# Filter data for BANKNIFTY options
banknifty_data = data[data["BANKNIFTY_symbol"] == "BANKNIFTY"]

# Create a list of unique dates from the original data
unique_dates = list(set(banknifty_data.index.date.astype(str)))
unique_dates.sort()

# Create a dropdown widget for date selection
date_selector = widgets.Dropdown(
    options=unique_dates,
    description='Select Date:',
)

# Specify the starting times for the different timeframes
start_time_5min = "09:15:00"
start_time_10min = "09:20:00"
start_time_15min = "09:15:00"

timeframes = [5, 10, 15]  # Different timeframes in minutes
timeframe_names = ['5 Min', '10 Min', '15 Min']  # Names for the timeframes

# Function to plot candlestick chart with price lines and max OI strike lines
def plot_candlestick_and_max_oi_strike_with_price_lines(date):
    for i, (timeframe, timeframe_name) in enumerate(zip(timeframes, timeframe_names)):
        # Filter data for the selected date
        selected_data = banknifty_data[banknifty_data.index.date.astype(str) == date]

        # Determine the appropriate start time based on the selected timeframe
        if timeframe == 5:
            start_time = start_time_5min
        elif timeframe == 10:
            start_time = start_time_10min
        elif timeframe == 15:
            start_time = start_time_15min

        # Create time intervals based on the selected timeframe and start time
        interval_minutes = timeframe
        start_datetime = pd.Timestamp(f"{date} {start_time}")
        time_intervals = pd.date_range(start=start_datetime, end=f"{date} 15:30:00", freq=f'{interval_minutes}T')

        # Initialize an empty DataFrame to store OHLC data
        ohlc_data = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close'])

        # Initialize empty lists to store CE and PE maximum OI strike prices at each time interval
        ce_max_oi_strike_list = []
        pe_max_oi_strike_list = []

        # Loop through each time interval
        for j in range(len(time_intervals) - 1):
            start_time = time_intervals[j]
            end_time = time_intervals[j + 1]

            # Filter data for the current time interval
            interval_data = selected_data[(selected_data.index >= start_time) & (selected_data.index < end_time)]

            if not interval_data.empty:
                # Calculate OHLC values for this interval
                open_price = interval_data.iloc[0]['Open']
                close_price = interval_data.iloc[-1]['Close']
                high_price = interval_data['High'].max()
                low_price = interval_data['Low'].min()

                # Append the calculated values to the OHLC data
                ohlc_data.loc[start_time] = [open_price, high_price, low_price, close_price]

                # Separate data for CE and PE
                ce_data = interval_data[interval_data["optiontype"] == "CE"]
                pe_data = interval_data[interval_data["optiontype"] == "PE"]

                # Find the strike with the highest OI for CE and PE
                ce_strike_with_highest_oi = ce_data[ce_data["oi"] == ce_data["oi"].max()]
                pe_strike_with_highest_oi = pe_data[pe_data["oi"] == pe_data["oi"].max()]

                # Append the maximum OI strike prices to the lists
                ce_max_oi_strike_list.append(ce_strike_with_highest_oi["strike"].values[0] if not ce_strike_with_highest_oi.empty else None)
                pe_max_oi_strike_list.append(pe_strike_with_highest_oi["strike"].values[0] if not pe_strike_with_highest_oi.empty else None)

        # Combine OHLC and maximum OI strike price data into a single DataFrame
        combined_data = pd.concat([ohlc_data, pd.Series(ce_max_oi_strike_list, name='CE Max OI Strike', index=time_intervals[:-1]),
                                   pd.Series(pe_max_oi_strike_list, name='PE Max OI Strike', index=time_intervals[:-1])], axis=1)

        # Create the candlestick chart with maximum OI strike lines
        s = mpf.make_mpf_style(
            marketcolors=mpf.make_marketcolors(up='#26a69a', down='#ef5350', edge='inherit', wick='inherit'),
            gridcolor='gray',  # Color of grid lines
            gridstyle='dotted',  # Style of grid lines
            rc={'lines.linewidth': 0.5},  # Adjust line width (make it smaller)
        )

        # Define the addplot parameter for price lines and max OI strike lines
        addplot = [
            mpf.make_addplot(combined_data['Close'] + 149, panel=0, color='#A0B3CE'),  # Price +100
            mpf.make_addplot(combined_data['Close'] - 149, panel=0, color='#CDA7A0'),   # Price -100
            mpf.make_addplot(combined_data['Close'] + 249, panel=0, color='#97CB9D'), # Price +200
            mpf.make_addplot(combined_data['Close'] - 249, panel=0, color='#EECFAE'),# Price -200
            mpf.make_addplot(combined_data['CE Max OI Strike'], panel=0, color='#ef5350', scatter=True, markersize=20),  # CE Max OI Strike
            mpf.make_addplot(combined_data['PE Max OI Strike'], panel=0, color='#26a69a', scatter=True, markersize=20), # PE Max OI Strike
        ]

        # Create the candlestick chart with custom Y-axis ticks, title, and addplot
        plt.figure(figsize=(20, 10))
        mpf.plot(combined_data, type='candle', title=f"{timeframe_name} BANKNIFTY Candlestick Chart with Max OI Strikes ({date})",
                 ylabel='Price', style=s, xrotation=0, addplot=addplot)

# Streamlit app UI
st.title("Candlestick Chart Viewer with Max OI Strikes")
st.sidebar.header("Select Date")

# Interactive widget for date selection
date = st.sidebar.selectbox("Select Date:", unique_dates)

# Display the candlestick chart based on the selected date
plot_candlestick_and_max_oi_strike_with_price_lines(date)
