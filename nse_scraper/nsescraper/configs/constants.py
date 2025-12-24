
HOME_URL = "httpshttps://www.nseindia.com/"
HISTORICAL_DATA_URL = "https://www.bseindia.com/markets/equity/EQReports/StockPrcHistori.aspx"

SEARCH_URL = "https://www.nseindia.com/api/NextApi/search/autocomplete"

BROWSER_IMPERSONATION = ["chrome", "safari", "firefox", "edge99", "edge101"]

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    # Add more recent versions if needed
            ]

delay_range = (2, 5)

max_attempts = 3

keep_cols = [['Open', 'High', 'Low', 'Close', 'Volume']]