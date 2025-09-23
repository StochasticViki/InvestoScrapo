from __future__ import division, print_function
from investoscrapo.client import InvestingClient

instance = InvestingClient()

lis = instance.Search("Reliance Industries")
print(lis)

sample_list = [{'id': 9235, 'url1': '/equities/reliance-steel---aluminum-co.', 'description': 'Reliance Steel & Aluminum Co', 'symbol': 'RS', 'exchange': 'NYSE', 'flag': 'USA', 'type': 'Stock - NYSE'}, 
                 {'id': 18367, 'url': '/equities/reliance-industries', 'description': 'Reliance Industries Ltd', 'symbol': 'RELI', 'exchange': 'NSE', 'flag': 'India', 'type': 'Stock - NSE'}, 
                 {'id': 1131514, 'url': '/equities/reliance-global', 'description': 'Reliance Global Group Inc', 'symbol': 'RELI', 'exchange': 'NASDAQ', 'flag': 'USA', 'type': 'Stock - NASDAQ'}]
# df = instance.Download_Historical(sample_list, "2020-03-31", "2025-03-31")
# print(df)