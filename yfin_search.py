from yahooquery import search as yq_search

def yahoo_finance_search(query):
    """
    Search for securities using Yahoo Finance
    
    Args:
        query (str): Search term (company name or symbol)
    
    Returns:
        list: List of dictionaries with standardized format matching investing.com structure
              Each dict contains: id, description, symbol, exchange, type
    """
    try:
        # Call yahooquery search
        raw_results = yq_search(query)
        
        # Check if quotes exist in results
        if 'quotes' not in raw_results or not raw_results['quotes']:
            return []
        
        # Convert Yahoo format to standardized format
        standardized_results = []
        
        for item in raw_results['quotes']:
            # Extract relevant fields
            result = {
                'id': item.get('symbol', ''),  # Use symbol as unique ID
                'description': item.get('longname') or item.get('shortname', 'N/A'),
                'symbol': item.get('symbol', 'N/A'),
                'exchange': item.get('exchange', 'N/A'),
                'type': item.get('quoteType', 'N/A'),  # e.g., EQUITY, ETF, etc.
            }
            
            standardized_results.append(result)
        
        return standardized_results
    
    except Exception as e:
        print(f"Error searching Yahoo Finance: {e}")
        return []


results = yahoo_finance_search("Apple")

print(f"Found {len(results)} results:\n")

for r in results:
    print(f"Description: {r['description']}")
    print(f"Symbol: {r['symbol']}")
    print(f"Exchange: {r['exchange']}")
    print(f"Type: {r['type']}")
    print("-" * 50)