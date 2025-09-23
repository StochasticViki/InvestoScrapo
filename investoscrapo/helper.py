import random
from investoscrapo.configs.constants import *
import time


def get_headers():
    return {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.8",
        "Domain-Id": "www",
        "Origin": "https://www.investing.com",
        "Priority": "u=1, i",
        "Referer": "https://www.investing.com/",
        "Sec-Ch-Ua": '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-Gpc": "1",
        "User-Agent": random.choice(user_agents),
    }

def add_delay():
            """Add random delay to avoid rate limiting."""
            delay = random.uniform(*delay_range)
            time.sleep(delay)
