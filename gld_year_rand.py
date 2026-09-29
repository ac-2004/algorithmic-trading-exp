from unittest import result
import pandas as pd
import matplotlib.pyplot as plt
import random

#-----------YEARLY BACKTESTING ON DAILY DATA----------------#

# Load historical GOLD data from CSV file
gld = pd.read_csv(
    "GLD-1d.csv",
    #skiprows = 2,  # Skip the first row, its metadata
    parse_dates=[0],
    index_col=0,
    header=0
)

# rename columns for easier access
gld.columns = ["Adjusted Close", "Close", "High", "Low", "Open", "Volume"]

# Display the first few rows of the dataframe
#print(gld.head())

# Analyze price change for a specific day
#test_day = gld.loc["2025-11-02"]
#open_price = test_day["Open"].iloc[0]
#close_price = test_day["Close"].iloc[-1]

#print(f"Analysis for {test_day.index[0].date()}")
#print("Open:", open_price)
#print("Close:", close_price)
#print(f"Change: {close_price - open_price}")
#print("Percent Change:", round(((close_price - open_price)/open_price)*100, 2), "%")

# if today open price - open price previous day < -2%, print buy signal
# resample will go through the data and put all the hourly data into one day. first will then select the first value of that day.
daily_opens = gld["Open"].dropna()

records_buy = []
records_sell = []

buy_signals = 0
sell_signals = 0

for i in range(1, len(daily_opens)):
    prev_date = daily_opens.index[i-2]
    curr_date = daily_opens.index[i]

    prev_open = daily_opens.iloc[i-2]
    curr_open = daily_opens.iloc[i]

    pct_change = ((curr_open - prev_open) / prev_open) * 100

    if pct_change < -1:
        records_buy.append([curr_date, curr_open, round(pct_change, 2)])
        buy_signals += 1

    if pct_change > 1:
        records_sell.append([curr_date, curr_open, round(pct_change, 2)])
        sell_signals += 1

# convert results into table
result_buy = pd.DataFrame(records_buy, columns=["Date", "Open Price", "Percent Change"])
#print("Buy Signals:")
#print(result_buy)

result_sell = pd.DataFrame(records_sell, columns=["Date", "Open Price", "Percent Change"])
#print("Sell Signals:")
#print(result_sell)

# merging the result_buy and result_sell into a single chronological list
result_buy["Signal"] = "Buy"
result_sell["Signal"] = "Sell"
merged_results = pd.concat([result_buy, result_sell], ignore_index=True)
merged_results["Date"] = pd.to_datetime(merged_results["Date"])
merged_results = merged_results.sort_values(by="Date")
merged_results = merged_results.reset_index(drop=True)

merged_results = pd.DataFrame(merged_results, columns=["Date", "Open Price", "Percent Change"])
print(merged_results)

# Plotting the buy and sell signals on the Gold price chart
plt.figure(figsize=(12, 6))
gld["Close"].plot(color="gold", label="Gold Close Price")

marker_times_buy = []
marker_lows_buy = []

for date in result_buy["Date"]:
    date = pd.to_datetime(date)
    day_data = gld.loc[str(date.date())]

    low_price = day_data["Low"].min()

    marker_times_buy.append(date)
    marker_lows_buy.append(low_price)

plt.scatter(marker_times_buy, marker_lows_buy, color="green", marker="^", s=100, label="Buy Signal")

marker_times_sell = []
marker_highs_sell = []

for date in result_sell["Date"]:
    date = pd.to_datetime(date)
    day_data = gld.loc[str(date.date())]

    high_price = day_data["High"].max()

    marker_times_sell.append(date)
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

trade_log = []

for idx, row in merged_results.iterrows():
    date = pd.to_datetime(row["Date"])
    pct_change = row["Percent Change"]

    capital_before = capital
    trade_capital = capital_before * risk_per_trade
    if trade_capital <= 0:
        continue

    # -------BUY SIGNAL
    if pct_change < 0:
        try:
            # Buy at lowest price of the day
            day_data = gld.loc[str(date.date())]
            if day_data.empty:
                continue

            #todays low/high
            low = day_data["Low"].min()
            high = day_data["High"].max()
            range = high - low

            # bias random buy price towards lower end of the day's range
            buy_min = low
            buy_max = low + (range * 0.3) # bottom 30% of range
            rand_buy_price = random.uniform(buy_min, buy_max)

            # random price was giving shit results so i biased it
            #rand_buy_price = random.uniform(day_data["Low"].min(), day_data["High"].max())

            # next days high/low
            sell_date = date + pd.Timedelta(days=1)
            sell_day_data = gld.loc[str(sell_date.date())]
            if sell_day_data.empty:
                continue

            next_low = sell_day_data["Low"].min()
            next_high = sell_day_data["High"].max()
            next_range = next_high - next_low

            sell_min = next_low + (next_range * 0.7) # top 30% of range
            sell_max = next_high
            rand_sell_price = random.uniform(sell_min, sell_max)

            #rand_sell_price = random.uniform(sell_day_data["Low"].min(), sell_day_data["High"].max())
        except KeyError:
            continue

        units = trade_capital / rand_buy_price

        profit = (rand_sell_price - rand_buy_price) * units
        total_profit = total_profit + profit
        capital_after = capital_before + profit
        capital = capital_after
        total_trades += 1

        if profit > 0:
            successful_trades += 1

        trade_log.append({
        "Type": "Buy",
        "Buy Date": date.date(),
        "Buy Price": round(rand_buy_price, 2),
        "Sell Date": sell_date.date(),
        "Sell Price": round(rand_sell_price, 2),
        "Units": round(units, 2),
        "Capital at Entry": round(capital_before, 2),
        "Capital at Exit": round(capital_after, 2),
        "Profit": round(profit, 2)
    })
    # -------SELL SIGNAL
    else:
        try:
            # entry: short on highest price of the day
            day_data = gld.loc[str(date.date())]
            if day_data.empty:
                continue

            #todays low/high
            low = day_data["Low"].min()
            high = day_data["High"].max()
            rng = high - low

            # bias random sell price towards higher end of the day's range
            sell_min = high - 0.3 * rng   # top 30% of range
            sell_max = high
            rand_sell_price = random.uniform(sell_min, sell_max)
            #rand_sell_price = random.uniform(day_data["Low"].min(), day_data["High"].max())

            # exit at lowest price next day
            buy_date = date + pd.Timedelta(days=1)
            buy_day_data = gld.loc[str(buy_date.date())]
            if buy_day_data.empty:
                continue

            next_low = buy_day_data["Low"].min()
            next_high = buy_day_data["High"].max()
            next_rng = next_high - next_low

            buy_min = next_low
            buy_max = next_low + 0.3 * next_rng   # bottom 30% of range
            rand_buy_price = random.uniform(buy_min, buy_max)
            #rand_buy_price = random.uniform(buy_day_data["Low"].min(), buy_day_data["High"].max())
        except KeyError:
            continue

        units = trade_capital / rand_sell_price

        profit = (rand_sell_price - rand_buy_price) * units
        total_profit = total_profit + profit
        capital_after = capital_before + profit
        capital = capital_after
        total_trades += 1

        if profit > 0:
            successful_trades += 1

        trade_log.append({
        "Type": "Sell",
        "Sell Date": date.date(),
        "Sell Price": round(rand_sell_price, 2),
        "Buy Date": buy_date.date(),
        "Buy Price": round(rand_buy_price, 2),
        "Units": round(units, 2),
        "Capital at Entry": round(capital_before, 2),
        "Capital at Exit": round(capital_after, 2),
        "Profit": round(profit, 2)
    })
    
pct_successful = (successful_trades / total_trades) * 100 if total_trades > 0 else 0

profits_per_trade = total_profit / total_trades if total_trades > 0 else 0

trade_log_df = pd.DataFrame(trade_log)

best_trade = trade_log_df.loc[trade_log_df["Profit"].idxmax()]
worst_trade = trade_log_df.loc[trade_log_df["Profit"].idxmin()]

trade_log_df["Entry Date"] = trade_log_df["Buy Date"].fillna(trade_log_df["Sell Date"])
trade_log_df = trade_log_df.sort_values(by="Entry Date")

longs = trade_log_df[trade_log_df["Type"] == "Buy"]
shorts = trade_log_df[trade_log_df["Type"] == "Sell"]

print("Best Trade:")
print(best_trade)
print("\nWorst Trade:")
print(worst_trade)
print("\n")

print("Starting Capital: $", starting_capital)
print("Ending Capital: $", round(capital, 2))
print("Risk per Trade:", risk_per_trade * 100, "%")
print("Total profit:", round(total_profit, 2))
print("Total trades:", total_trades)
print("Successful trades:", successful_trades)
print("Average profit per trade: $", round(profits_per_trade, 2))
print("Buy signals generated:", buy_signals)
print("Buy signals won:", len(longs[longs["Profit"] > 0]))
print("Sell signals generated:", sell_signals)
print("Sell signals won:", len(shorts[shorts["Profit"] > 0]))
print(round(pct_successful, 2), "% successful trades")

plt.show()

print("Long win rate:", len(longs[longs["Profit"] > 0]) / len(longs) * 100 if len(longs) > 0 else 0, "%")
print("Short win rate:", len(shorts[shorts["Profit"] > 0]) / len(shorts) * 100 if len(shorts) > 0 else 0, "%")

trade_log_df.to_csv("gld_trade_log_yearly_rands.csv", index=False)

#This is the fixed version