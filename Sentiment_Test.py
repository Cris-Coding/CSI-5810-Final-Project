#SENTIMENT TEST
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
import requests

#historical article initialization
def fetch_av_news(ticker, start_date_str, api_key):
    URL= (
        f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
        f"&tickers={ticker}"
        f"&time_from={start_date_str}T0000"
        f"&sort=RELEVANCE"
        f"&limit=300"
        f"&apikey={api_key}"
    )
    try:
        response= requests.get(URL)
        response.raise_for_status()
        data= response.json()
        
        if "feed" not in data:
            print("\n API Error: ", data)
        
        return data.get('feed', [])
    
    except requests.exceptions.RequestException as e:
        print(f"Error Code: {e}")
        return[]
        

#Downloading Lexicon for Vader
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')
    
#Configuring the Ticker
ticker= "NVDA"
months_back= 12
start_date= datetime.now()- timedelta(days= months_back* 30)
yf_start_str= start_date.strftime('%Y-%m-%d') #converting to standard format
av_start_str= start_date.strftime('%Y%m%d')
AV_API_KEY= "VCYC51C73B9Z4WK6"

#Getting Stock Data
print(f"Getting Data on {ticker}...")
stock= yf.Ticker(ticker)
history_df= stock.history(start= yf_start_str)

#Data Cleaning and Processing
history_df= history_df.reset_index()
history_df['Date']= pd.to_datetime(history_df['Date']).dt.date
print(f"Stock History: {len(history_df)} rows")

#Collecting Text Data for Sentiment Analysis
news_list= fetch_av_news(ticker, av_start_str, AV_API_KEY)
analyzer= SentimentIntensityAnalyzer()
scored_news= []
print(f"Found {len(news_list)} recent articles")

if news_list:
    for article in news_list:
        title = article.get('title', '')
        summary = article.get('summary', '')
        date_string = article.get('time_published', None)
        
        if date_string is None:
            continue
        
        try:
            date_object= pd.to_datetime(date_string).date()
            
        except Exception:
            continue
        
        capt= f"{title}.{summary}"
        scores= analyzer.polarity_scores(capt)
        compound_score= scores['compound']
    
        scored_news.append({
            'Date': date_object,
            'Title': title,
            'Sentiment': compound_score
        })
        
        
#Creating Dataframe, Merging and Correlating
news_df= pd.DataFrame(scored_news)
print(news_df.head)

if news_df is not None:
    daily_sentiment= news_df.groupby('Date')['Sentiment'].mean().reset_index()
    
    #merging dataset
    merged_df= pd.merge(history_df, daily_sentiment, on= 'Date', how= 'inner')
    
    if not merged_df.empty:
        print(f"\nSuccessfully merged {len(merged_df)} days of overlapping data")
        correlation= merged_df['Close'].corr(merged_df['Sentiment']) #Correlation Calculation
        print(f"\n*** Correlation between Close Price and Sentiment: {correlation:.4f} ***")
    
