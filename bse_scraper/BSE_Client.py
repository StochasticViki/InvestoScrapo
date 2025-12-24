import json
import datetime
from curl_cffi import requests
import math
import time
import pandas as pd
from urllib.parse import urlencode, quote_plus
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ALL_COMPLETED, as_completed, wait
import random
from bs4 import BeautifulSoup, Tag
from bse_scraper.bsescraper.configs.constants import HOME_URL, HISTORICAL_DATA_URL, SEARCH_URL,BROWSER_IMPERSONATION, user_agents, keep_cols, delay_range
from bse_scraper.bsescraper.utils.logger import get_logger

logging = get_logger(__name__)

def get_headers():
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.6",
        "Connection": "keep-alive",
        "Host": "api.bseindia.com",
        "Origin": "https://www.bseindia.com",
        "Referer": "https://www.bseindia.com/",
        "Sec-Ch-Ua": '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-Gpc": "1",
        "User-Agent": random.choice(user_agents),
    }

def get_headers_adjusted(params):
    query_string = urlencode(params)
    return {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "www.bseindia.com",
    "Origin": "https://www.bseindia.com",
    "Pragma": "no-cache",
    "Referer": f"{HISTORICAL_DATA_URL}?{query_string}",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": random.choice(user_agents),
    }

def add_delay():
            """Add random delay to avoid rate limiting."""
            delay = random.uniform(*delay_range)
            time.sleep(delay)


class bse_scraper():

    def __init__(self):       
        self.session = requests.Session()
        self.session.headers.update(get_headers())
        self.max_retries = 3
        self.cookies = None

    def fetch_cookies(self):
        """Fetch initial cookies and bypass Cloudflare if needed."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                with requests.Session(impersonate=random.choice(BROWSER_IMPERSONATION)) as s:              
                    response = s.get(HOME_URL, timeout=30)
                    logging.info(f"Cookie fetch attempt {attempt + 1}: Status {response.status_code}")
                
                    if response.status_code == 403:
                        logging.warning("Cloudflare challenge detected. Waiting...")
                        soup = BeautifulSoup(response.text, 'html.parser')
                        challenge_form = soup.find('form', {'id': 'challenge-form'})
                        if challenge_form:
                            time.sleep(5)  # Wait for challenge to process
                            response = s.get(HOME_URL, timeout=30)
                    
                    if response.status_code == 200:
                        self.cookies = self.session.cookies.get_dict()
                        logging.info("Successfully fetched cookies")
                        return self.cookies
                    else:
                        logging.warning(f"Attempt {attempt + 1} failed with status {response.status_code}")
                        if attempt < max_attempts - 1:
                            time.sleep(5)  # Wait before retry
                            
            except Exception as e:
                logging.error(f"Cookie fetch attempt {attempt + 1} error: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(5)
                    
        raise ValueError("Failed to initialize session after all attempts")

    def fetch_search_results(self, search_term: str):

        def extract_name(tag):
            name = []
            for child in tag.children:
                if isinstance(child, Tag) and child.name == 'br':
                    break
                name.append(child.get_text(strip=True) if isinstance(child, Tag) else child.strip())
            return ''.join(filter(None, name))
        
        params = {"Type": "EQ",
                  "text": search_term,
                  "flag": "site"}
        suggestions = []
        try:
            add_delay()  # Add delay between requests to mimic human behavior
            self.session.cookies.update(self.cookies)
            
            response = self.session.get(SEARCH_URL, params=params, timeout=30)
            
            if response.status_code == 200:
                try:
                    soup = BeautifulSoup(response.text, "html.parser")
                    # print(soup)
                    results = soup.select("li[class*='quotemenu']")
                    
                    for li in results:
                        anchor = li.find("a")
                        if not anchor:
                            continue

                        # Get the full name line (Company name + INDUSTRIES LTD etc.)
                        full_name = extract_name(anchor)
                        
                        # Get the span text: contains ISIN and scrip code
                        span = anchor.find("span")
                        if span:
                            parts = span.get_text(separator=" ", strip=True).split()
                            isin = next((x for x in parts if x.startswith("INE")), None)
                            scrip_code = next((x for x in parts if x.isdigit()), None)
                        else:
                            isin = scrip_code = None

                        co_dict = {
                            "description": full_name,
                            "isin": isin,
                            "id": scrip_code}
                        suggestions.append(co_dict)
                    return suggestions

                except ValueError as ve:
                    logging.exception("structure of response error: %s", ve)
                    raise
            
            elif response.status_code == 403:
                logging.warning("Access forbidden. Updating cookies and retrying...")

            else:
                logging.error(
                    "Failed fetch. URL: %s | Status: %s | Response: %s",
                    SEARCH_URL, response.status_code, response.text
                )
        except Exception as e:
            print(f"Error with search URL {SEARCH_URL}: {e}")
            return None

    def request_data(self, scrip_dict, start_date, end_date):
        """
        Fetch historical data for a given scrip between specified dates.
        
        Args:
            scrip_dict: Dictionary containing scrip info with keys 'id' and 'description'
            start_date: Start date in format 'YYYY-MM-DD'
            end_date: End date in format 'YYYY-MM-DD'
        
        Returns:
            pandas.DataFrame: Historical price data
        """
        
        if not self.cookies:
            self.cookies = self.fetch_cookies()
        
        scrip_url = HISTORICAL_DATA_URL
        params = {
            "expandable": 7,                            
            "scripcode": scrip_dict["id"],           
            "flag": "sp",                         
            "Submit": "G"
        }
        
        headers = get_headers_adjusted(params)
        
        for attempt in range(self.max_retries):
            try:
                add_delay()
                with requests.Session(impersonate=random.choice(BROWSER_IMPERSONATION)) as s:
                    
                    # Update headers and cookies
                    s.headers.update(headers)
                    s.cookies.update(self.cookies)        
                    logging.info(f"Fetching data for {scrip_dict.get('description', 'Unknown')} (ID: {scrip_dict['id']}) - Attempt {attempt + 1}")
                    
                    # Initial GET request to get form data
                    get_response = s.get(scrip_url, params=params, timeout=30)

                    if get_response.status_code == 200:
                        logging.info("Status code 200: Initial response received.")
                        
                        get_soup = BeautifulSoup(get_response.text, "html.parser")
                        
                        # Extract required form fields
                        viewstate = get_soup.select_one('input[name="__VIEWSTATE"]')
                        eventvalidation = get_soup.select_one('input[name="__EVENTVALIDATION"]')
                        viewstategenerator = get_soup.select_one('input[name="__VIEWSTATEGENERATOR"]')
                        
                        if not all([viewstate, eventvalidation, viewstategenerator]):
                            logging.error("Failed to extract required form fields")
                            continue
                        
                        viewstate_val = viewstate['value']
                        eventvalidation_val = eventvalidation['value']
                        viewstategenerator_val = viewstategenerator['value']
                        
                        logging.info("All payloads extracted successfully")
                        
                        # Parse and format dates
                        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                        
                        # Format dates for BSE (DD/MM/YYYY)
                        bse_start_date = start_date_obj.strftime("%d/%m/%Y")
                        bse_end_date = end_date_obj.strftime("%d/%m/%Y")
                        
                        # Current timestamp for BSE format
                        current_timestamp = datetime.now().strftime("%d/%m/%Y 12:00:00 AM")
                        
                        logging.info(f"Date range: {bse_start_date} to {bse_end_date}")
                        
                        # Construct the final payload for POST request
                        final_payload = {
                            "__EVENTTARGET": "",
                            "__EVENTARGUMENT": "",
                            "__VIEWSTATE": viewstate_val,
                            "__VIEWSTATEGENERATOR": viewstategenerator_val,
                            "__VIEWSTATEENCRYPTED": "",
                            "__EVENTVALIDATION": eventvalidation_val,
                            
                            # Core scrip and date fields
                            "ctl00$ContentPlaceHolder1$hdnCode": scrip_dict["id"],
                            "ctl00$ContentPlaceHolder1$hiddenScripCode": scrip_dict["id"],
                            "ctl00$ContentPlaceHolder1$hidCompanyVal": scrip_dict["description"],
                            
                            # Date-related fields
                            "ctl00$ContentPlaceHolder1$txtFromDate": bse_start_date,
                            "ctl00$ContentPlaceHolder1$txtToDate": bse_end_date,
                            "ctl00$ContentPlaceHolder1$hidFromDate": bse_start_date,
                            "ctl00$ContentPlaceHolder1$hidToDate": bse_end_date,
                            "ctl00$ContentPlaceHolder1$hidCurrentDate": current_timestamp,
                            
                            # Frequency selection - IMPORTANT: This ensures daily data
                            "ctl00$ContentPlaceHolder1$DMY": "rdbDaily",
                            "ctl00$ContentPlaceHolder1$hidDMY": "D",
                            "ctl00$ContentPlaceHolder1$hdflag": "0",
                            
                            # Search fields
                            "ctl00$ContentPlaceHolder1$smartSearch": scrip_dict["description"],
                            "ctl00$ContentPlaceHolder1$scripname": scrip_dict["description"],
                            "ctl00$ContentPlaceHolder1$Hidden4": scrip_dict["description"],
                            
                            # Settlement calendar
                            "ctl00$ContentPlaceHolder1$ddlsetllementcal": "0",
                            
                            # Other required fields
                            "ctl00$ContentPlaceHolder1$DDate": "",
                            "ctl00$ContentPlaceHolder1$hidYear": "",
                            "ctl00$ContentPlaceHolder1$hidOldDMY": "",
                            "ctl00$ContentPlaceHolder1$Hidden1": "",
                            
                            # Submit button - this should trigger the CSV download
                            "ctl00$ContentPlaceHolder1$btnSubmit": "Submit"
                        }
                        
                        # Make the final POST request
                        query_string = urlencode(params)
                        scrip_url_final = f"{scrip_url}?{query_string}"
                        
                        logging.info("Submitting final request for historical data...")
                        final_response = s.post(scrip_url_final, data=final_payload, timeout=60)
                        
                        if final_response.status_code == 200:
                            logging.info("Final response received successfully")
                            
                            # Check if response is CSV data
                            content_type = final_response.headers.get('content-type', '').lower()
                            content_disposition = final_response.headers.get('content-disposition', '')
                            
                            if 'excel' in content_type or 'csv' in content_disposition:
                                logging.info("✅ Received CSV data response")
                                
                                try:
                                    # Parse CSV data using pandas
                                    from io import StringIO
                                    csv_data = StringIO(final_response.text)
                                    
                                    # Read CSV with pandas
                                    df = pd.read_csv(csv_data, parse_dates=['Date'], dayfirst=True)
                                    
                                    if len(df) > 0:
                                        logging.info(f"✅ Successfully parsed CSV with {len(df)} rows")
                                        
                                        # Clean column names (remove extra spaces)
                                        df.columns = df.columns.str.strip()
                                        
                                        # Ensure Date column is properly formatted
                                        if 'Date' in df.columns:
                                            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
                                            
                                            # Filter data to requested date range
                                            df = df[
                                                (df['Date'] >= start_date_obj) & 
                                                (df['Date'] <= end_date_obj)
                                            ]
                                            
                                            # Sort by date
                                            df = df.sort_values('Date')
                                        
                                        # Convert numeric columns (handle commas in numbers)
                                        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Last', 'Prevclose', 'Volume', 'Turnover']
                                        for col in numeric_cols:
                                            if col in df.columns:
                                                # Remove commas and convert to numeric
                                                df[col] = df[col].astype(str).str.replace(',', '').str.replace('-', '0')
                                                df[col] = pd.to_numeric(df[col], errors='coerce')
                                        
                                        # Add symbol information
                                        df['Symbol'] = scrip_dict.get('description', 'Unknown')
                                        df['ScripCode'] = scrip_dict['id']
                                        
                                        # Remove any completely empty rows
                                        df = df.dropna(how='all')
                                        
                                        logging.info(f"✅ Data processing complete. Final dataset has {len(df)} rows")
                                        logging.info(f"Date range in data: {df['Date'].min()} to {df['Date'].max()}")
                                        
                                        return df
                                    else:
                                        logging.warning("CSV data is empty")
                                        
                                except Exception as csv_error:
                                    logging.error(f"Error parsing CSV data: {str(csv_error)}")
                                    # Fallback: save raw response for debugging
                                    with open(f"debug_csv_{scrip_dict['id']}.txt", "w", encoding="utf-8") as f:
                                        f.write(final_response.text)
                                    logging.info("Raw CSV response saved for debugging")
                            
                            else:
                                logging.info("Response is HTML, attempting to parse tables...")
                                
                                # Parse the response as HTML (fallback)
                                final_soup = BeautifulSoup(final_response.text, "html.parser")
                                
                                # Find the data table - look for table with historical data
                                data_table = None
                                tables = final_soup.find_all("table")
                                
                                for table in tables:
                                    table_text = table.get_text()
                                    if "Date" in table_text and ("Open" in table_text or "Close" in table_text):
                                        # Check if this table has actual data rows
                                        data_rows = table.find_all("tr")
                                        if data_rows:
                                            data_table = table
                                            break
                                
                                if data_table:
                                    logging.info("✅ Found the target data table in HTML")
                                    
                                    # Extract headers
                                    headers = []
                                    header_rows = data_table.find_all("tr")
                                    
                                    for row in header_rows:
                                        header_cells = row.find_all("td", class_="innertable_header1")
                                        if header_cells:
                                            headers = [cell.get_text(strip=True).replace('\n', ' ') for cell in header_cells]
                                            headers.remove("* Spread")
                                            break
                                    
                                    if not headers:
                                        # Fallback header extraction
                                        headers = None
                                    
                                    logging.info(f"Headers extracted: {headers}")
                                    
                                    # Extract data rows
                                    data_rows = data_table.find_all("tr", class_="TTRow")
                                    all_data = []
                                    
                                    for row in data_rows:
                                        cols = row.find_all("td")
                                        if len(cols) >= 5:  # Ensure we have enough columns
                                            row_data = [col.get_text(strip=True) for col in cols]
                                            all_data.append(row_data)
                                    
                                    if all_data:
                                        logging.info(f"✅ Extracted {len(all_data)} data rows from HTML")
                                        # Create DataFrame
                                        df = pd.DataFrame(all_data, columns=headers)
                                        # Clean and process the data
                                        if 'Date' in df.columns:
                                            # Convert date column to datetime
                                            df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
                                            
                                            # Filter data to requested date range
                                            df = df[
                                                (df['Date'] >= start_date_obj) & 
                                                (df['Date'] <= end_date_obj)
                                            ]
                                            
                                            # Sort by date
                                            df = df.sort_values('Date')
                                        
                                        # Convert numeric columns
                                        for col in keep_cols:
                                            if col in df.columns:
                                                df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce')
                                        
                                        # Add symbol information
                                        df['Symbol'] = scrip_dict.get('description', 'Unknown')
                                        df['ScripCode'] = scrip_dict['id']
                                        
                                        logging.info(f"✅ Data processing complete. Final dataset has {len(df)} rows")
                                        return df
                                    
                                    else:
                                        logging.warning("No data rows found in the HTML table")
                                
                                else:
                                    logging.warning("Could not find data table in HTML response")
                                    # Debug: Save response to file for inspection
                                    with open(f"debug_response_{scrip_dict['id']}.html", "w", encoding="utf-8") as f:
                                        f.write(final_response.text)
                                    logging.info("Response saved to debug file for inspection")
                        
                        else:
                            logging.warning(f"Final request failed with status code {final_response.status_code}")
                            if final_response.status_code == 403:
                                logging.info("Access forbidden - refreshing cookies...")
                                self.cookies = self.fetch_cookies()
                            
                    else:
                        logging.warning(f"Initial request failed with status code {get_response.status_code}")
                        if get_response.status_code == 403:
                            logging.info("Access forbidden - refreshing cookies...")
                            self.cookies = self.fetch_cookies()
            
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed with error: {str(e)}")
                if attempt < self.max_retries - 1:
                    logging.info("Retrying after delay...")
                    time.sleep(5)
                else:
                    logging.error("All retry attempts exhausted")
                    raise
        
        logging.error("Failed to fetch data after all attempts")
        return None
        
        

start_date = "2025-05-23"
end_date = "2025-06-23"

# instance = bse_scraper()
# sample = {'description': 'RELIANCE INDUSTRIES LTD', 'isin': 'INE002A01018', 'id': '500325'}
# # dict = instance.fetch_search_results("Reliance")
# # print(dict)
# df = instance.request_data(sample, start_date, end_date)
# df.to_excel("prices.xlsx")