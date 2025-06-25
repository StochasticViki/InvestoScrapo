
HOME_URL = "https://www.investing.com/"
HISTORICAL_DATA_URL = "https://api.investing.com/api/financialdata/historical/"

search_urls = [
                "https://api.investing.com/api/search/v2/search",
                "https://api.investing.com/api/search",
                "https://www.investing.com/search/service/searchTopResults"
            ]

BROWSER_IMPERSONATION = ["chrome", "safari", "firefox", "edge99", "edge101"]

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    ]

delay_range = (2, 5)

max_attempts = 3

keep_cols = ["rowDate", "last_closeRaw", "symbol"]