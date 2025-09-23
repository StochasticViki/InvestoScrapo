import json
from curl_cffi import requests
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, ALL_COMPLETED, as_completed, wait
import random
from bs4 import BeautifulSoup
from investoscrapo.utils.logger import get_logger
from investoscrapo.configs.constants import *
from investoscrapo.helper import *



logger = get_logger(__name__)

class Investing():

    def __init__(self):       
        self.session = requests.Session()
        self.session.headers.update({
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-Gpc": "1"})
        
        self.max_retries = 3
        self.cookies = None

    def fetch_cookies(self):
        """Fetch initial cookies and bypass Cloudflare if needed."""
        
        for attempt in range(max_attempts):
            try:
                # Update headers for each attempt
                self.session.headers.update(get_headers())
                
                response = self.session.get(HOME_URL, timeout=30)
                logger.info(f"Cookie fetch attempt {attempt + 1}: Status {response.status_code}")
                
                if response.status_code == 403:
                    logger.warning("Cloudflare challenge detected. Waiting...")
                    soup = BeautifulSoup(response.text, 'html.parser')
                    challenge_form = soup.find('form', {'id': 'challenge-form'})
                    if challenge_form:
                        time.sleep(5)  # Wait for challenge to process
                        response = self.session.get(HOME_URL, timeout=30)
                
                if response.status_code == 200:
                    self.cookies = self.session.cookies.get_dict()
                    logger.info("Successfully fetched cookies")
                    return self.cookies
                else:
                    logger.warning(f"Attempt {attempt + 1} failed with status {response.status_code}")
                    if attempt < max_attempts - 1:
                        time.sleep(5)  # Wait before retry
                        
            except Exception as e:
                logger.error(f"Cookie fetch attempt {attempt + 1} error: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(5)
                    
        raise ValueError("Failed to initialize session after all attempts")

    def fetch_search_results(self, search_term):
        if not self.cookies:
           self.cookies = self.fetch_cookies()
        for search_url in search_urls:
            params = {"q": search_term}
            
            try:
                add_delay()  # Add delay between requests to mimic human behavior
                self.session.cookies.update(self.cookies)
                
                response = self.session.get(search_url, params=params, timeout=30)
                
                if response.status_code == 200:
                    # decompressed = brotli.decompress(response.content)
                    try:
                        data = response.json()
                        if data.get("quotes"):
                            return data["quotes"]  # Return first matching quote
                        else:
                            logger.error(
                                "No quotes found. URL: %s | Status: %s | Response: %s",
                                search_url, response.status_code, response.text
                            )
                            raise ValueError("No results found. Try a different search term.")
                    except ValueError as ve:
                        logger.exception("JSON decoding or structure error: %s", ve)
                        print(f"[DEBUG] URL: {response.url}")
                        print(f"[DEBUG] Status Code: {response.status_code}")
                        print(f"[DEBUG] Response Headers: {response.headers}")
                        print(f"[DEBUG] Response Text (first 200 chars): {response.text[:200]}")
                    
                        raise
                
                elif response.status_code == 403:
                    logger.warning("Access forbidden. Updating cookies and retrying...")
                    continue

                else:
                    logger.error(
                        "Failed fetch. URL: %s | Status: %s | Response: %s",
                        search_url, response.status_code, response.text
                    )

            except Exception as e:
                print(f"Error with search URL {search_url}: {e}")
                continue

        return None

    def request_data(self, scrip_dict, start_date, end_date):
        
        if not self.cookies:
           self.cookies = self.fetch_cookies()
        
        scrip_url = HISTORICAL_DATA_URL + str(scrip_dict["id"])
        params = {
        "start-date": start_date,         # Starting date of historical data
        "end-date": end_date,             # Ending date of historical data
        "time-frame": "Daily",            # Frequency: Daily, Weekly, Monthly
        "add-missing-rows": "false"}      # If false, skips non-trading days (e.g., weekends, holidays)
        
        headers = get_headers()
        
        for attempt in range(self.max_retries):
            try:
                add_delay()
                with requests.Session(impersonate=random.choice(BROWSER_IMPERSONATION)) as s:
                    
                    # Update headers and cookies
                    s.headers.update(headers)
                    s.cookies.update(self.cookies)        
                    logger.info(f"Fetching data for {scrip_dict.get('symbol', 'Unknown')} (ID: {scrip_dict['id']}) - Attempt {attempt + 1}")
                    response = s.get(scrip_url, params=params, timeout=30)

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            logger.info(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                            
                            # Handle different response structures
                            if isinstance(data, dict):
                                if "data" in data and data["data"]:
                                    df = pd.DataFrame(data["data"])
                                    df['symbol'] = scrip_dict.get('symbol', 'Unknown')
                                    df['instrument_id'] = scrip_dict['id']
                                    logger.info(f"Successfully fetched {len(df)} rows for {scrip_dict.get('symbol')}")
                                    return df
                                elif isinstance(data, list):
                                    df = pd.DataFrame(data)
                                    df['symbol'] = scrip_dict.get('symbol', 'Unknown')
                                    df['instrument_id'] = scrip_dict['id']
                                    logger.info(f"Successfully fetched {len(df)} rows for {scrip_dict.get('symbol')}")
                                    return df
                                else:
                                    logger.warning(f"Unexpected data structure: {data}")
                                    return pd.DataFrame()
                            else:
                                logger.warning(f"Response is not a dictionary: {type(data)}")
                                return pd.DataFrame()
                                
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error: {e}")
                            logger.error(f"Response content: {response.text[:500]}")
                            return pd.DataFrame()
                            
                    elif response.status_code == 403:
                        logger.warning("403 Forbidden - refreshing cookies and retrying...")
                        if 'cf-chl-bypass' in response.text:
                            pass
                        self.cookies = self.fetch_cookies()
                        continue
                        
                    else:
                        logger.error(f"Failed to fetch data. Status: {response.status_code}")
                        logger.error(f"Response: {response.text[:500]}")
                        if attempt < self.max_retries - 1:
                            continue
                        else:
                            return pd.DataFrame()
                            
            except Exception as e:
                logger.error(f"Error fetching data (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    continue
                else:
                    return pd.DataFrame()
                    
        return pd.DataFrame()

    def threaded_request(self, list_dict: list[dict],  start_date: str, end_date: str) -> pd.DataFrame:
        result = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {
                executor.submit(self.request_data, scrip_dict, start_date, end_date): scrip_dict 
                for scrip_dict in list_dict
            }
            wait(future_to_url, return_when=ALL_COMPLETED)
            for future in as_completed(future_to_url):
                data = future_to_url[future]
                try:
                    df = future.result()[keep_cols]
                    result.append(df)
                except Exception as exc:
                    logger.error('%r generated an exception: %s. Please try again later.' % (data, exc))
                    raise exc
                
        return result