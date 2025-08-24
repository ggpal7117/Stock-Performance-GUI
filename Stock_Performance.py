import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import streamlit as st
import sys
import lxml
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import wikipedia
import os
# Acess all SP500 Tickers/Companies
tickers_df = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
tickers = tickers_df.Symbol.tolist()
tickers_df["Name"] = tickers_df["Security"] + " - " + tickers_df["GICS Sector"]
tickers_to_name = dict(zip(tickers_df["Symbol"], tickers_df["Name"]))

temp = tickers_df.copy()
temp = temp.sort_values(by = "Symbol")
tickers_to_security = dict(zip(temp["Symbol"], temp["Security"]))

# # Range Shift for Future Close Prices
range_shift = {i : i*-21 for i in range(1,301)} # 1 month = 21 trading days up to 300 months(25 years)

# # Access All Possible Data
@st.cache_data
def load_data():
    all_stock_data = pd.DataFrame()
    #base_dir = os.path.join(os.path.dirname(__file__), "data")  # look inside repo
    downloads_dir = os.path.expanduser("~/Downloads/Data")  # look inside Downloads/Data folder
    # Loop through years and concatenate data
    for year in range(2015, 2026):
        file_path = file_path = os.path.join(downloads_dir, f"{year}_stock_data.csv")
        temp = pd.read_csv(file_path)
        all_stock_data = pd.concat([all_stock_data, temp], ignore_index=True)

    all_stock_data["Date"] = pd.to_datetime(all_stock_data["Date"])

    # Filter stocks with 10 years of data
    grouped_dates = all_stock_data.copy()
    grouped_dates['Year'] = grouped_dates['Date'].dt.year

    g = grouped_dates.groupby('Ticker')['Year'].agg(['min', 'max']).reset_index()
    g['Diff'] = g['max'] - g['min']
    tickers_to_use = g.query('Diff >= 10').Ticker.tolist()

    return all_stock_data.query('Ticker in @tickers_to_use')


all_stock_data = load_data()

@st.cache_data
def returns_and_volatility_info(time_range, return_period):
    """
    Input: 
        Time Range for how much stock data the user wants to simulate. Ex --> '6M'
        Return Period. How far into the future does the user want the returns
    Output: 
        {'Avg_return', 'Avg_Std', "Quartiles"}

    Example:
        time_range = 5(assumed months)
        return_period = 1 month --> shift close prices -21
    """
    global all_stock_data
    global range_shift
    
    # Precompute future close prices for all tickers at once
    temp = all_stock_data.copy()
    temp["Future_Close"] = (
        temp.groupby("Ticker")["Close"]
        .shift(range_shift[return_period])
    )

    # Filter last `time_range` months
    latest_dates = temp.groupby("Ticker")["Date"].transform("max")
    months_ago = latest_dates - pd.DateOffset(months=time_range)
    df_filtered = temp[temp["Date"] >= months_ago]

    # Compute returns
    df_filtered["Return"] = 100 * (
        (df_filtered["Future_Close"] - df_filtered["Close"]) / df_filtered["Close"]
    )

    # Aggregate
    agg_stats = (
        df_filtered.dropna(subset=["Return"])
        .groupby("Ticker")["Return"]
        .agg(["mean", "std"])
    )

    return (df_filtered, agg_stats.reset_index())

@st.cache_data
def compute_stats(aggregated_states):
    # Compute summary statistics
    stats = pd.Series({
        "Mean Return": aggregated_states["mean"].mean(),
        "40% Return": aggregated_states["mean"].quantile(0.40),
        "75% Return": aggregated_states["mean"].quantile(0.75),
        "Mean Std Dev": aggregated_states["std"].mean(),
        "40% Std Dev": aggregated_states["std"].quantile(0.40),
        "75% Std Dev": aggregated_states["std"].quantile(0.75)
    })

    return stats

@st.cache_data
def valid_stock(return_range, volatility_range, time_range, return_period):
    """
    Input: Return and Volatility Ranges to Subset the Data. Appropriate time ranges
    Output: Df with all valid stocks
    """
    l_return_range, h_return_range = return_range[0], return_range[1]
    l_vol_range, h_vol_range = volatility_range[0], volatility_range[1]
    
    returns_volatility = returns_and_volatility_info(time_range, return_period)[1]
    returns_volatility = returns_volatility[
        (returns_volatility['mean'] >= l_return_range)
        &
        (returns_volatility['mean'] < h_return_range)
    ]

    returns_volatility = returns_volatility[
        (returns_volatility['std'] >= l_vol_range)
        &
        (returns_volatility['std'] < h_vol_range)
    ]

    returns_volatility = returns_volatility.sort_values(by = ["mean", "std"], ascending = [False, True])
    print(f"Length of Valid Stock df: {len(returns_volatility)}")

    return (returns_volatility)


# Create Function to Plot top 5 Stocks
@st.cache_data
def find_valid_stocks(time_range, return_period, returns_option, volatility_option): # 4, 1
    """
    inputs:
        time_range: length of simulation(must be at least 2 times of return period)
        return_period: expected trading period
        returns + volatility options: strs from low to high
    outputs:
        df of all appropriate/valid stocks
    """
    historical_data = returns_and_volatility_info(time_range, return_period)[0]
    #display(historical_data)
    #print(historical_data.dtypes)
    ticker_returns_volatility = returns_and_volatility_info(time_range, return_period)[1]
    ticker_stats = compute_stats(ticker_returns_volatility)

    # print(f"Ticker Stats:\n{ticker_stats}")
    
    mean_return = ticker_stats["Mean Return"]
    mean_std = ticker_stats["Mean Std Dev"]

    # Create return ranges
    if returns_option == "Low Returns":
        ret_range = [-sys.maxsize - 1, ticker_stats["40% Return"]]
    elif returns_option == "Medium Returns":
        ret_range = [ticker_stats["40% Return"], ticker_stats["75% Return"]]
    elif returns_option == "High Returns":
        ret_range = [ticker_stats["75% Return"], sys.maxsize]

    # Create volatility ranges
    if volatility_option == "Low Volatility":
        vol_range = [-sys.maxsize - 1, ticker_stats["40% Std Dev"]]
    elif volatility_option == "Medium Volatility":
        vol_range = [ticker_stats["40% Std Dev"], ticker_stats["75% Std Dev"]]
    elif volatility_option == "High Volatility":
        vol_range = [ticker_stats["75% Std Dev"], sys.maxsize]

    valid_tickers = valid_stock(ret_range, vol_range, time_range, return_period)
    if returns_option == "Low Returns":
        valid_tickers = valid_tickers.sort_values(by = ["mean", "std"], ascending = [True, False])
    elif volatility_option == "High Volatility" and returns_option != "Low Returns":
        valid_tickers = valid_tickers.sort_values(by = ["std", "mean"], ascending = [False, False])

    plotting_data=valid_tickers.head()
    plotting_tickers=plotting_data.Ticker


    valid_tickers.columns = ["Ticker", "Mean Returns", "std"]
    valid_tickers["Name"] = valid_tickers["Ticker"].map(tickers_to_name)
    return valid_tickers[["Ticker", "Name", "Mean Returns", "std"]], historical_data.query('Ticker in @plotting_tickers').set_index("Date"), plotting_tickers, mean_return

@st.cache_data
def query_stock(time_range, return_period, ticker):
    """Create Function to Find Historical Returns Data of a Specific Ticker"""
    returns_volatility_total = returns_and_volatility_info(time_range, return_period)[0]
    ticker_return_data = returns_volatility_total.query('Ticker == @ticker')
    return (ticker_return_data)


# print(find_valid_stocks(24, 12, "High Returns", "Low Volatility"))
ticker_to_industry = dict(zip(tickers_df["Symbol"], tickers_df['GICS Sector']))

@st.cache_data
# Industry Performance
def industry_stats(time_range, return_period):
    df = returns_and_volatility_info(time_range, return_period)[1]
    df.columns = ["Ticker", "Mean_Returns", "Dev_Returns"]
    df["Industry"] = df['Ticker'].map(ticker_to_industry) 
    df = df.groupby('Industry', as_index=False)[["Mean_Returns", "Dev_Returns"]].mean()
    return df.sort_values(by = ["Mean_Returns", "Dev_Returns"], ascending = [False, True])



def main():
    st.set_page_config(page_title="Simulation App", layout="centered")

    # Sidebar Navigation
    page = st.sidebar.radio("📂 Navigate", ["Stock Performance Analysis", "Individual Stock Performance", "Industry Performance"])

    # -------------------------
    # PAGE 1: Stock Performance Analysis
    # -------------------------
    if page == "Stock Performance Analysis":
        # --- Page Title --
        st.title("💹 Stock Performance Analysis")
        st.write("This page allows you to simulate stock performance based on historical data.")
        st.write("You can select different return and volatility ranges to find valid stocks for your investment strategy.")
        st.write("Data is from 8/22/2015 - 8/22/2025")

        # --- Inputs ---
        returns_choice = st.radio("📈 Select Returns", ["Low Returns", "Medium Returns", "High Returns"])
        volatility_choice = st.radio("🌊 Select Volatility", ["Low Volatility", "Medium Volatility", "High Volatility"])
        return_length = st.slider("⏱️ Return Period (months)", min_value=1, max_value=15, value=1, step=1)
        timeframe = st.slider("📅 Simulation Timeframe (months)",
                            min_value=2*return_length,
                            max_value=8*return_length,
                            value=2*return_length,
                            step=1)

        # --- Submit + Show Results ---
        if st.button("✅ Run Simulation"):
            st.success("Simulation Running...")

            # --- Call your function ---
            valid_df = find_valid_stocks(
                int(timeframe), int(return_length), str(returns_choice), str(volatility_choice)
            )[0]

            # Show dataframe
            st.subheader("📊 Valid Stocks Table")
            st.dataframe(valid_df)

            # Plot top 5 stocks
            st.subheader("📈 Stock Performance Charts")
            st.write("The first column shows the candlestick chart for each stock, while the second column displays the returns over time.")
            st.write("The red dashed line represents the mean return of the SP500 ticker during the specified simulation timeframe for appropriate return range.")
            st.write("Graphs will takes a few seconds to load...")

            plotting_data = find_valid_stocks(timeframe, return_length, returns_choice, volatility_choice)[1]
            plotting_tickers = find_valid_stocks(timeframe, return_length, returns_choice, volatility_choice)[2]
            mean_return = find_valid_stocks(timeframe, return_length, returns_choice, volatility_choice)[3]

            fig, ax = plt.subplots(5, 2, figsize=(15, 25))
            for i, tick in enumerate(plotting_tickers):
                candlestick_data = plotting_data.query('Ticker == @tick')[['Open', 'High', 'Low', 'Close']]
                returns = plotting_data.query('Ticker == @tick')[["Return"]]

                # Candle Stick Plot
                mpf.plot(candlestick_data, type='candle', ax=ax[i][0],style="blueskies")
                ax[i][0].set_title(f"{tick}\n{tickers_to_name[tick]}")
                ax[i][0].grid(alpha=0.5, linestyle='--', color='k')

                # Returns plot
                return_plot = returns.plot(ax=ax[i][1])
                return_plot.axhline(y=0, color='k', linestyle='--', linewidth=1)
                return_plot.axhline(y=mean_return, color='red', linestyle='--', linewidth=1, label="Mean Return of SP500 Ticker")
                return_plot.set_ylabel("Returns")

                # Compute Mean/STD
                ticker_returns_volatility = returns_and_volatility_info(timeframe, return_length)[1]
                mean_return_ticker = float(ticker_returns_volatility.query('Ticker == @tick')["mean"])
                std_return_ticker = float(ticker_returns_volatility.query('Ticker == @tick')["std"])

                return_plot.set_title(f"Average Return: {mean_return_ticker:.2f} | Dev Return: {std_return_ticker:.2f}")
                return_plot.set_xlabel("Date")
                return_plot.grid(alpha=0.5, linestyle='--', color='k')
                return_plot.legend()

            plt.tight_layout()
            plt.subplots_adjust(hspace=0.45, wspace=0.35)

            st.pyplot(fig)
            st.success("Simulation Complete!")

    # -------------------------
    # PAGE 2: Individual Stock Performance
    # -------------------------
    elif page == "Individual Stock Performance":
        st.title("📊 Individual Stock Performance")
        st.write("This page allows you to explore trends for indivdual stock tickers.")
        
        ticker = st.selectbox("Choose an option:", sorted(tickers_df.Security.tolist()))
        return_length = st.slider("⏱️ Return Period (months)", min_value=1, max_value=15, value=1, step=1)
        timeframe = st.slider("📅 Simulation Timeframe (months)",
                            min_value=2*return_length,
                            max_value=8*return_length,
                            value=2*return_length,
                            step=1)
        
        # st.write(return_length, timeframe, ticker)

        symbol = tickers_df.query('Security == @ticker')['Symbol'].values[0]
        stock_df = query_stock(timeframe, return_length, symbol)

        fig = make_subplots(
            rows=1,
            cols=2,
            horizontal_spacing=0.25,
            subplot_titles=(
                f"{ticker}: Candlestick Plot", 
                f"Average Return: {stock_df.Return.mean():.2f}  |  Dev Return: {stock_df.Return.std():.2f}"
            ),
            column_widths=[0.6, 0.4]
        )

        # --- Candlestick Trace ---
        fig.add_trace(
            go.Candlestick(
                x=stock_df.Date,
                open=stock_df.Open,
                high=stock_df.High,
                low=stock_df.Low,
                close=stock_df.Close,
                name="Candlestick"
            ),
            row=1, col=1
        )

        # --- Return Line Plot ---
        returns_stock_df = stock_df[["Date", 'Return']].dropna()
        fig.add_trace(
            go.Scatter(
                x=returns_stock_df.Date,
                y=returns_stock_df.Return,
                mode='lines',
                name='Return'
            ),
            row=1, col=2
        )

        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Returns", row=1, col=2)

        fig.update_layout(
            title_text=f"{symbol} Stock Overview",
            height =650,
            width=1350
        )
        st.plotly_chart(fig)
        
        # Wikipedia Search
        st.subheader(f"📖 About {ticker}")

        try:
            # Try more specific name first (ticker + sector)
            specific_name = ticker + " - " + tickers_df.query('Symbol == @symbol')['GICS Sector'].values[0]
            try:
                wiki_str = wikipedia.summary(specific_name, sentences=5)
            except wikipedia.exceptions.DisambiguationError:
                # fallback if specific name still ambiguous
                wiki_str = wikipedia.summary(ticker, sentences=5)

            st.write(wiki_str)

        except wikipedia.exceptions.DisambiguationError as e:
            st.warning(f"⚠️ Multiple possible matches found for **{ticker}**. Try one of these: {', '.join(e.options[:5])}...")
        except wikipedia.exceptions.PageError:
            st.warning("🚫 No Wikipedia page found for this stock.")
        except Exception as e:
            st.warning(f"An error occurred while fetching Wikipedia info: {str(e)}")


    # -------------------------
    # PAGE 3: Industry Performance
    # -------------------------
    elif page == "Industry Performance":
        st.title("🏭 Industry Performance Analysis")
        st.write("This page allows you to explore performance trends across different industries (GICS Sectors) in the S&P 500.")
        st.write("You can select the return period and simulation timeframe to see how various industries have performed historically.")
        st.write("Data is from 8/22/2015 - 8/22/2025")

        # --- Inputs ---
        return_length = st.slider("⏱️ Return Period (months)", min_value=1, max_value=15, value=1, step=1)
        timeframe = st.slider("📅 Simulation Timeframe (months)",
                            min_value=2*return_length,
                            max_value=8*return_length,
                            value=2*return_length,
                            step=1)
        
        industry_df = industry_stats(timeframe, return_length)

        industry_df["Mean_Returns"] = industry_df["Mean_Returns"].round(2)
        industry_df["Dev_Returns"] = industry_df["Dev_Returns"].round(2)

        

        st.subheader("📊 Industry Performance Table")
        st.dataframe(industry_df)
        # Format text annotations for bars

        all_data = returns_and_volatility_info(timeframe, return_length)[0]
        all_data["Industry"] = all_data['Ticker'].map(ticker_to_industry)
        
        bar_tab, box_tab = st.tabs(["📊 Industry Bar Chart", "📦 Industry Box Plots"])
        with box_tab:
            st.subheader("📦 Industry Returns Distribution")
            fig = px.box(
                all_data.dropna(subset=["Return"]),
                x="Industry",
                y="Return",
                title="Industry Returns Distribution",
                labels={
                    "Return": "Returns",
                    "Industry": "GICS Sector"
                },
                height=775,
                width=1200,
                color = "Industry",
                points = False  # Show outliers
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, theme="streamlit")
        with bar_tab:
            st.subheader("📊 Industry Mean Returns with Volatility")
            fig = px.bar(
                industry_df,  # Use the modified DataFrame
                x='Industry',
                y='Mean_Returns',
                error_y='Dev_Returns',
                title="Industry Mean Returns",
                labels={
                    "Mean_Returns": "Mean Returns",
                    "Industry": "GICS Sector",
                    "Dev_Returns": "Volatility (Std Dev)"
                },
                height=600,
                width=1000,
                hover_data=["Mean_Returns", "Dev_Returns"]  # Only show these in hover
            )


            # Position text above bars
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig)
                                            
if __name__ == "__main__":
    main() 
