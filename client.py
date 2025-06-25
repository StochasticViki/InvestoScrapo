from scraper import Investing
from utils.transformer import *
from utils.logger import get_logger
import pandas as pd

logger = get_logger()

class InvestorClient():
    def __init__(self):
        self.scraper = Investing()
    
    def Search(self, Term: str) -> list[dict]:
        return self.scraper.fetch_search_results(Term)
    
    def Download_Historical(self, selected_list_dicts: list[dict], start_date: str, end_date: str) -> pd.DataFrame:
        raw = self.scraper.threaded_request(selected_list_dicts, start_date, end_date)
        processed_df = clean_dataframe(raw)
        return processed_df