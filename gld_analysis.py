from unittest import result
import pandas as pd
import matplotlib.pyplot as plt

# Load historical GOLD data from CSV file
gld = pd.read_csv(
    "GLD-1h.csv",
    skiprows = 2,  # Skip the first row, its metadata
    parse_dates=[0],
    index_col=0,
    header=0
)

# rename columns for easier access
gld.columns = ["Adjusted Close", "Close", "High", "Low", "Open", "Volume"]

# Display the first few rows of the dataframe
#print(gld.head())

# Analyze price change for a specific day
test_day = gld.loc["2025-11-02"]
open_price = test_day["Open"].iloc[0]
close_price = test_day["Close"].iloc[-1]

#print(f"Analysis for {test_day.index[0].date()}")
#print("Open:", open_price)
#print("Close:", close_price)
#print(f"Change: {close_price - open_price}")
#print("Percent Change:", round(((close_price - open_price)/open_price)*100, 2), "%")

# if today open price - open price next day < -2%, print buy signal
# resample will go through the data and put all the hourly data into one day. first will then select the first value of that day.
daily_opens = gld["Open"].resample("1D").first().dropna()

records_buy = []
records_sell = []

for i in range(1, len(daily_opens)):
    prev_date = daily_opens.index[i-2]
    curr_date = daily_opens.index[i]

    prev_open = daily_opens.iloc[i-2]
    curr_open = daily_opens.iloc[i]

    pct_change = ((curr_open - prev_open) / prev_open) * 100

    if pct_change < -1:
        records_buy.append([curr_date, curr_open, round(pct_change, 2)])

    if pct_change > 1:
        records_sell.append([curr_date, curr_open, round(pct_change, 2)])

# convert results into table
result_buy = pd.DataFrame(records_buy, columns=["Date", "Open Price", "Percent Change"])
print("Buy Signals:")
print(result_buy)

result_sell = pd.DataFrame(records_sell, columns=["Date", "Open Price", "Percent Change"])
print("Sell Signals:")
print(result_sell)

lowest_prices = []

for date in result_buy["Date"]:
    date = pd.to_datetime(date)
    day_data = gld.loc[str(date.date())]
    low_price = day_data["Low"].iloc[-1]
    lowest_prices.append(low_price)

lowest_prices = pd.DataFrame(lowest_prices, columns=["Low"])
print(lowest_prices)

highest_prices = []
for date in result_sell["Date"]:
    date = pd.to_datetime(date)
    day_data = gld.loc[str(date.date())]
    high_price = day_data["High"].iloc[0]
    highest_prices.append(high_price)

highest_prices = pd.DataFrame(highest_prices, columns=["High"])
print(highest_prices)

plt.figure(figsize=(12, 6))
gld["Close"].plot(color="gold", label="Gold Close Price")

marker_times_buy = []
marker_lows_buy = []

for date in result_buy["Date"]:
    date = pd.to_datetime(date)
    day_data = gld.loc[str(date.date())]
    low_time = day_data["Low"].idxmin()
    low_price = day_data["Low"].min()

    marker_times_buy.append(low_time)
    marker_lows_buy.append(low_price)

plt.scatter(marker_times_buy, marker_lows_buy, color="green", marker="^", s=100, label="Buy Signal")

marker_times_sell = []
marker_highs_sell = []

for date in result_sell["Date"]:
    date = pd.to_datetime(date)
    day_data = gld.loc[str(date.date())]
    high_time = day_data["High"].idxmax()
    high_price = day_data["High"].max()

    marker_times_sell.append(high_time)
    marker_highs_sell.append(high_price)

plt.scatter(marker_times_sell, marker_highs_sell, color="red", marker="v", s=100, label="Sell Signal")

plt.title("Gold (GLD) Hourly Close Prices with Buy Signals")
plt.legend()
plt.grid(True)


# testing the strategy
# at each buy signal, buy at the lowest price of that day, sell at the highest price after 2 days
starting_capital = 100000
capital = starting_capital
risk_per_trade = 0.6 # 60% of capital per trade

total_profit = 0
successful_trades = 0
total_trades = 0
pct_successful = 0

for date in result_buy["Date"]:
    date = pd.to_datetime(date)
    day_data = gld.loc[str(date.date())]
    if day_data.empty:
        continue
    buy_price = day_data["Low"].min()

    sell_date = date + pd.Timedelta(days=1)
    sell_day_data = gld.loc[str(sell_date.date())]
    if sell_day_data.empty:
        continue
    sell_price = sell_day_data["High"].max()

    trade_capital = capital * risk_per_trade

    if trade_capital <= 0:
        continue

    units = trade_capital / buy_price

    profit = (sell_price - buy_price) * units
    total_profit = total_profit + profit
    capital += profit
    total_trades += 1

    if profit > 0:
        successful_trades += 1

# now the opposite
for date in result_sell["Date"]:
    try:
        date = pd.to_datetime(date)
        day_data = gld.loc[str(date.date())]
        if day_data.empty:
            continue
        sell_price = day_data["High"].max()

        buy_date = date + pd.Timedelta(days=1)
        buy_day_data = gld.loc[str(buy_date.date())]
        if buy_day_data.empty:
            continue
        buy_price = buy_day_data["Low"].min()
    except KeyError:
        continue

    trade_capital = capital * risk_per_trade

    if trade_capital <= 0:
        continue

    units = trade_capital / sell_price

    profit = (sell_price - buy_price) * units
    total_profit = total_profit + profit
    capital += profit
    total_trades += 1

    if profit > 0:
        successful_trades += 1

pct_successful = (successful_trades / total_trades) * 100 if total_trades > 0 else 0

profits_per_trade = total_profit / total_trades if total_trades > 0 else 0

print("Starting Capital: $", starting_capital)
print("Ending Capital: $", round(capital, 2))
print("Total profit:", round(total_profit, 2))
print("Total trades:", total_trades)
print("Successful trades:", successful_trades)
print("Average profit per trade: $", round(profits_per_trade, 2))
print(round(pct_successful, 2), "% successful trades")

plt.show()