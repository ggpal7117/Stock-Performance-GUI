# Stock-Performance-GUI

## APP LINK: [https://stock-performance-gui-9mqz6jpkwjoztbqxsrhsdu.streamlit.app/](https://stock-performance-gui-imb552bmzoc9hsnzvk2blj.streamlit.app/)

In this project, I created an interactive dashboard using Streamlit to show the SP500 companies' performances over time. The first page shows all stocks that have low or high returns and volatility, plotting 5 stocks' closing prices and returns for a user's preferred return period, which is between 1-15 months. The simulation data consists of stock data from August 2015, providing robust information for return periods of every stock. 
The second page provides users a chance to learn more about individual stocks and companies with the same return and simulation range as the first page. 
The third page provides users a chance the learn which specific industries are performing well aswell as those that are underperforming. Just like the other two pages, users can enter a return period and a longer simulation range to base that return period on.


**Note: This is not stock trading advice. This dashboard is only meant for users to understand how certain companies are performing.**

**Note: Not all SP500 tickers are included, as some don't have 10 years of historical stock data, such as GE Vernova (GEV), which only went public in 2024.**


## Return Period vs Simulation Data
The return period is the period of time in months that a user wants to see returns. For example, if the return period is 1, then the algorithm will generate/calculate the 1-month returns(if I buy a stock now, and sell it exactly 1 month from now). The simulation data is essentially how much historical data you want to look back on. 
For example, if the time range/simulation data is 4 months and the return period is 1 month, the algorithm calculates all the 1-month returns based on this one month to assess its overall performance.


# Page 1
The first page, titled "Stock Performance Analysis," is where users can change both the return period and time range, all the way to 10 years of stock data. Users can also choose stocks ranging from low-high ranges and volatility to see which stocks may be growing consistently, or fluctuating heavily. Both a data frame aswell as a plot of 5 notable tickers are displayed based on the user's inputs.


# Page 2
The second page, called "Individual Stock Performance," is an extension of the previous page, where users can see the returns and volatility of every stock in the S&P 500. Towards the end of the page, the app sends an API call to the Wikipedia API and attempts to describe the company. 


# Page 3
The last page, "Industry Performance," shows which specific industries are performing well and poorly based on the user input time frame and return period. Two types of plots are available through a tab, an error bar chart showing returns of the stock, aswell as its Standard Deviation, and a box plot to better show the spread of data.

# Thank you
