#Article Keys
import requests
import json

# Replace with your Key
API_KEY = "VCYC51C73B9Z4WK6"
TICKER = "MSFT"

url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={TICKER}&limit=1&apikey={API_KEY}"

response = requests.get(url)
data = response.json()

# Get the first article from the 'feed' list
if "feed" in data and len(data["feed"]) > 0:
    article = data["feed"][0]
    
    print(f"--- Available Keys for an Article ---")
    # Print just the list of keys (attributes)
    print(list(article.keys()))
    
    print("\n--- Detailed Breakdown ---")
    # Print key and value to see what they look like
    for key, value in article.items():
        # format output nicely
        print(f"{key}: {str(value)[:100]}...") # Truncate long text
else:
    print("No articles found or API Limit reached.")