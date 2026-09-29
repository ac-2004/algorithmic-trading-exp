import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

# importing data
gld = pd.read_csv(
    "GLD-1h_2025.csv",
    parse_dates=[0],
    index_col=0,
    header=0
)

# rename columns for easier access
gld.columns = ["Close", "High", "Low", "Open", "Volume"]

'''
# some volume prices were outliers, getting rid of them
gld.loc[gld["Volume"] > 5000, "Volume"] = gld.loc[gld["Volume"] > 5000, "Volume"] / 100

# plot closing price and volume on separate y-axes
fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.plot(gld.index, gld["Close"], color="gold", label="GLD Close Price")
ax1.set_xlabel("Date")
ax1.set_ylabel("GLD Close Price", color="gold")

# twinx allows us to share the same x-axis but have a different y-axis
ax2 = ax1.twinx()
# .bar() creates vertical bars for volume
ax2.bar(gld.index, gld["Volume"], color="lightgray", alpha=0.5, label="GLD Volume")
ax2.set_ylabel("GLD Volume", color="lightgray")

plt.show()
'''

# plucking a price at a certain datetime
#price_at_2pm = gld.loc["2025-01-03 02:00:00", "Close"]
#print("Price at 2 PM on 2025-01-02:", price_at_2pm)

# identifynig large price movements within a small time period (4h) and analysing what happens afterwards

buy_signals = []
buy_markers = 0

for i, row in gld.iterrows():
    price_now = row["Open"]
    # get price 4 hours later
    try:
        price_4h_later = gld.loc[i + pd.Timedelta(hours=4), "Close"]
    except KeyError:
        continue

    pct_change = ((price_4h_later - price_now) / price_now) * 100
    if pct_change < -2:
        buy_signals.append([i, price_now, round(pct_change, 2)])
        buy_markers += 1

# convert results into table
buy_signals_df = pd.DataFrame(buy_signals, columns=["Datetime", "Open Price", "Percent Change"])
print("Buy Signals (4h price increase > 1%):")
print(buy_signals_df)

print("Total Buy Signals:", buy_markers)

plt.figure(figsize=(10, 5))
plt.plot(gld.index, gld["Close"], label="GLD Close Price", color="gold")
plt.scatter(buy_signals_df["Datetime"], buy_signals_df["Open Price"], color="green", marker="^", s=100, label="Buy Signal")
plt.xlabel("Date")
plt.ylabel("GLD Close Price")
plt.title("GLD Buy Signals Based on 4h Price Increase > 1%")
plt.legend()
plt.show()