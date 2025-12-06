#AV STOCK SENTIMENT ANALYSIS
import tkinter as tk
from tkinter import messagebox
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests

# --- BACKEND LOGIC ---
def fetch_av_news(ticker, start_date_str, limit, api_key):
    URL = (
        f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
        f"&tickers={ticker}"
        f"&time_from={start_date_str}T0000"
        f"&sort=LATEST" 
        f"&limit={limit}"
        f"&apikey={api_key}"
    )
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "feed" not in data: return None, data 
        return data.get('feed', []), None
    except requests.exceptions.RequestException as e:
        return None, str(e)

def analyze_stock_sentiment(ticker, months_back, api_limit, api_key):
    try:
        start_date = datetime.now() - timedelta(days=int(months_back) * 30)
    except ValueError: return "Error: Months must be number.", None, None
        
    yf_start_str = start_date.strftime('%Y-%m-%d')
    av_start_str = start_date.strftime('%Y%m%d')

    stock = yf.Ticker(ticker)
    try:
        history_df = stock.history(start=yf_start_str)
    except Exception: return "Yahoo Finance Error", None, None
    
    if history_df.empty: return "No stock data.", None, None

    history_df = history_df.reset_index()
    history_df['Date'] = pd.to_datetime(history_df['Date']).dt.date

    news_list, error = fetch_av_news(ticker, av_start_str, api_limit, api_key)
    if error: return f"API Error: {error}", None, None
    
    daily_sentiment = pd.DataFrame(columns=['Date', 'Sentiment'])

    if news_list:
        scored_news = []
        for article in news_list:
            date_string = article.get('time_published', None)
            if not date_string: continue
            try:
                date_object = pd.to_datetime(date_string).date()
            except: continue

            ticker_specific_score = 0.0
            found_specific = False
            
            if 'ticker_sentiment' in article:
                for item in article['ticker_sentiment']:
                    if item['ticker'] == ticker:
                        ticker_specific_score = float(item['ticker_sentiment_score'])
                        found_specific = True
                        break
            
            if not found_specific:
                ticker_specific_score = float(article.get('overall_sentiment_score', 0))

            scored_news.append({'Date': date_object, 'Sentiment': ticker_specific_score})

        news_df = pd.DataFrame(scored_news)
        if not news_df.empty:
            daily_sentiment = news_df.groupby('Date')['Sentiment'].mean().reset_index()

    merged_df = pd.merge(history_df, daily_sentiment, on='Date', how='left')
    merged_df['Sentiment'] = merged_df['Sentiment'].fillna(0)

    if merged_df.empty: return "No data after merge.", None, None

    if merged_df['Sentiment'].std() == 0:
        correlation = 0.0 
    else:
        correlation = merged_df['Close'].corr(merged_df['Sentiment'])
    
    return None, merged_df, correlation

# --- UI SETUP ---
def run_analysis():
    result_text.set("Running analysis...")
    for widget in graph_frame.winfo_children(): widget.destroy()
    plt.close('all') 
    root.update() 

    t_symbol = ticker_entry.get().upper().strip()
    m_back = months_entry.get()
    a_limit = limit_entry.get()
    MY_API_KEY = "VCYC51C73B9Z4WK6" 

    if not t_symbol or not m_back or not a_limit:
        messagebox.showerror("Error", "Missing fields.")
        return

    error_msg, df, corr = analyze_stock_sentiment(t_symbol, m_back, a_limit, MY_API_KEY)
    if error_msg:
        result_text.set(error_msg)
        return

    result_text.set(f"AV Model: {t_symbol}\nData Points: {len(df)}\nCorrelation: {corr:.4f}")

    fig, ax1 = plt.subplots(figsize=(6, 4), dpi=100)
    color_price = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price ($)', color=color_price, fontweight='bold')
    ax1.plot(df['Date'], df['Close'], color=color_price, linewidth=2)
    ax1.tick_params(axis='y', labelcolor=color_price)
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')

    ax2 = ax1.twinx()  
    color_sent = 'tab:green'
    ax2.set_ylabel('AV Sentiment', color=color_sent, fontweight='bold')
    ax2.plot(df['Date'], df['Sentiment'], color=color_sent, linestyle='--', linewidth=1)
    ax2.tick_params(axis='y', labelcolor=color_sent)
    
    # --- THE FIX: LOCK SCALE TO -1 to 1 ---
    ax2.set_ylim(-1.1, 1.1)
    # --------------------------------------

    plt.title(f"{t_symbol} Price vs AV Sentiment")
    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

root = tk.Tk()
root.title("AlphaVantage Model Analyzer")
root.geometry("850x750")

input_frame = tk.Frame(root, padx=10, pady=15)
input_frame.pack(side=tk.TOP, fill=tk.X)

tk.Label(input_frame, text="Ticker:").grid(row=0, column=0, padx=5)
ticker_entry = tk.Entry(input_frame, width=10)
ticker_entry.grid(row=0, column=1, padx=5)

tk.Label(input_frame, text="Months:").grid(row=0, column=2, padx=5)
months_entry = tk.Spinbox(input_frame, from_=1, to=24, width=5)
months_entry.grid(row=0, column=3, padx=5)
months_entry.insert(0, 6)

tk.Label(input_frame, text="Limit:").grid(row=0, column=4, padx=5)
limit_entry = tk.Entry(input_frame, width=8)
limit_entry.insert(0, "100")
limit_entry.grid(row=0, column=5, padx=5)

tk.Button(input_frame, text="Analyze", command=run_analysis, bg="#e1e1e1").grid(row=0, column=6, padx=20)

result_text = tk.StringVar()
result_text.set("Ready.")
tk.Label(root, textvariable=result_text, bg="#f0f0f0", relief="sunken", pady=10).pack(side=tk.TOP, fill=tk.X, padx=15)

graph_frame = tk.Frame(root, bg="white", bd=2, relief="groove")
graph_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=15, pady=15)

root.mainloop()