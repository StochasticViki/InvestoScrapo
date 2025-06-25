# InvestoScrapo

A fast, multi-threaded web scraper to collect historical financial data from Investing.com, built with curl_cffi and pandas.

## Installation

To install with pip on macOS or Linux, run:

```bash
python3 -m pip install investoscrapo
```
To install with pip on Windows, run:

```bash
python -m pip install investoscrapo
```
## Quickstart Guide

```bash
from investoscrapo.client import InvestingClient

client = InvestingClient()
query = "Reliance Industries Limited"
search_results = client.Search(query)
prices = client.Download_Historical(search_results, "2020-01-01", "2024-01-01")

print(prices.head())
```
## Contribute

If you'd like to contribute to InvestoScrapo, check out https://github.com/StochasticViki/investoscrapo
