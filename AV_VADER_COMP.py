#AlphaVantage vs Vader
import requests
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt

# 1. Setup
nltk.download('vader_lexicon', quiet=True)
analyzer= SentimentIntensityAnalyzer()

API_KEY= "VCYC51C73B9Z4WK6" 
TICKER= "NVDA" 
LIMIT= 500

print(f"Fetching top {LIMIT} articles for {TICKER}...")
url = (
    f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
    f"&tickers={TICKER}&limit={LIMIT}&sort=LATEST&apikey={API_KEY}"
)

response = requests.get(url)
data = response.json()

if "feed" not in data:
    print("Error fetching data:", data)
else:
    print("Total Articles: ", len(data['feed']))
    comparison_data = []

    for article in data['feed']:
        ticker_specific_score= 0.0
        if 'ticker_sentiment' in article:
            for item in article['ticker_sentiment']:
                if item['ticker'] == TICKER:
                    ticker_specific_score = float(item['ticker_sentiment_score'])
                    break
        
        # error protection
        if ticker_specific_score== 0.0:
            ticker_specific_score= float(article.get('overall_sentiment_score', 0))

        # 2. Calculate VADER Score 
        title = article.get('title', '')
        summary = article.get('summary', '')
        text_mashup = f"{title}. {summary}"
        vader_score = analyzer.polarity_scores(text_mashup)['compound']
        
        comparison_data.append({
            'Title': title[:30] + "...",
            'AV_Ticker_Score': ticker_specific_score, # The targeted score
            'VADER_Score': vader_score,
            'Difference': abs(ticker_specific_score - vader_score)
        })

    # Create DataFrame
    df = pd.DataFrame(comparison_data)

    # Visualize
    plt.figure(figsize=(8, 6))
    plt.scatter(df['VADER_Score'], df['AV_Ticker_Score'], alpha= 0.6, color='purple')
    
    plt.axhline(0, color= 'black', linewidth= 1) # Zero Line (Y-axis)
    plt.axvline(0, color= 'black', linewidth= 1) # Zero Line (X-axis)
    plt.plot([-1, 1], [-1, 1], color='red', linestyle='--', label='Perfect Agreement')
    
    plt.title(f'VADER vs AlphaVantage (Targeted {TICKER} Sentiment)')
    plt.xlabel('Your VADER Score')
    plt.ylabel(f'AlphaVantage {TICKER} Specific Score')
    plt.grid(True, alpha= 0.3)
    plt.legend()
    plt.show()