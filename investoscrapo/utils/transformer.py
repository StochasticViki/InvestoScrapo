import openpyxl.reader
import pandas as pd
import numpy as np
import openpyxl
from openpyxl import Workbook
from functools import reduce
from investoscrapo.configs.constants import *

import pandas as pd

import pandas as pd

KEEP_COLS = [
    "rowDate",
    "last_closeRaw",
    "volumeRaw",
    "symbol",
    "instrument_id",
]

def build_full_panel_with_ids(dfs):
    """
    Build a time-aligned panel with MultiIndex columns:
      level 0: data field
      level 1: symbol (ticker)
    Includes static fields (symbol, instrument_id) repeated over time.
    """

    panels = []

    for df in dfs:
        # 1. Keep only required columns

        # 2. Type cleaning
        df["rowDate"] = pd.to_datetime(df["rowDate"], format="%b %d, %Y")
        df["last_closeRaw"] = df["last_closeRaw"].astype(float)
        df["volumeRaw"] = df["volumeRaw"].astype(float)

        # 3. Extract identifiers (constant per DF)
        symbol = df["symbol"].iloc[0]
        instrument_id = df["instrument_id"].iloc[0]

        # 4. Set date index
        df = df.set_index("rowDate")

        # 5. Build wide block INCLUDING static fields
        wide = pd.DataFrame(
            {
                ("last_closeRaw", symbol): df["last_closeRaw"],
                ("volumeRaw", symbol): df["volumeRaw"],
                ("symbol", symbol): symbol,
                ("instrument_id", symbol): instrument_id,
            },
            index=df.index,
        )

        panels.append(wide)

    # 6. Concatenate all tickers horizontally
    panel = pd.concat(panels, axis=1).sort_index()

    # 7. Ensure proper MultiIndex
    panel.columns = pd.MultiIndex.from_tuples(
        panel.columns, names=["field", "symbol"]
    )

    return panel


