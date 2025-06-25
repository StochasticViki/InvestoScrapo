import openpyxl.reader
import pandas as pd
import numpy as np
import openpyxl
from openpyxl import Workbook
from functools import reduce
from configs.constants import *

import pandas as pd

def clean_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    # Step 1: Split the wide dataframe into chunks of 3 columns (rowDate, last_closeRaw, symbol)
    dfs = []
    n_cols_per_stock = len(keep_cols)

    for i in range(0, raw_df.shape[1], n_cols_per_stock):
        stock_df = raw_df.iloc[:, i:i + n_cols_per_stock].copy()
        stock_df.columns = ["rowDate", "last_closeRaw", "symbol"]

        # Get the stock ticker (assumes same symbol in all rows)
        ticker = stock_df["symbol"].iloc[1]

        # Rename 'last_closeRaw' to the ticker name
        stock_df = stock_df[["rowDate", "last_closeRaw"]]
        stock_df.rename(columns={"last_closeRaw": ticker}, inplace=True)

        dfs.append(stock_df)
 
    df_merged = reduce(lambda left, right: pd.merge(left, right, on="rowDate"), dfs)

    return df_merged
    
