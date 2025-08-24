# Stock-Performance-GUI

## APP LINK: https://stock-performance-gui-9mqz6jpkwjoztbqxsrhsdu.streamlit.app/

In this project, I created an interactive dashboard using Streamlit to show the SP500 companies' performances over time. The first page shows all stocks that have low or high returns and volatility, plotting 5 stocks' closing prices and returns for a user's preferred return period, which is between 1-15 months. The simulation data consists of stock data from August 2015, providing robust information for return periods of every stock. 
The second page provides users a chance to learn more about individual stocks and companies with the same return and simulation range as the first page. 
The third page provides users a chance the learn which specific industries are performing well aswell as those that are underperforming. Just like the other two pages, users can enter a return period and a longer simulation range to base that return period on.


**Note: This is not stock trading advice. This dashboard is only meant for users to understand how certain companies are performing**


## Return Period vs Simulation Data
The return period is the period of time in months that a user wants to see returns. For example, if the return period is 1, then the algorithm will generate/calculate the 1-month returns(if I buy a stock now, and sell it exactly 1 month from now). The simulation data is essentially how much historical data you want to look back on. 
So, for example, if the time range/simulation data is 4 months, and the return period is 1 month, the algorithm will calculate all the 1-month returns based on this one month to see its overall performance.


# Main Algorithm
The main algorithm the app uses filters the aggregated data from 2015-2025 based on the simulation data range. The simulation data range is always 2 times greater than the return period.
