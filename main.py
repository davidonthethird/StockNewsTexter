import requests
from datetime import date
from twilio.rest import Client
import pandas as pd

# This Python script reads a CSV file containing desired stocks with their symbols and company names.
# It then uses the Alpha Vantage API to retrieve daily closing prices for the past two days.
# Next, it calculates the percentage change in price and fetches relevant news articles from the News API.
# Finally, depending on the price change and user configuration, it sends SMS notifications via Twilio
# containing stock symbol, price change, top 3 headlines, and corresponding news bodies.

# EXAMPLE OUTPUT
"""
AMZN: 🔺1.34
Headline: Opinion: How to design a US data privacy law
Body: Op-ed: Why you should care about the GDPR, and how the US could develop a better version.
Source: Ars Technica

AMZN: 🔺1.34
Headline: OpenAI asked US to approve energy-guzzling 5GW data centers, report says
Body: OpenAI stokes China fears to woo US approvals for huge data centers, report says.
Source: Ars Technica

AMZN: 🔺1.34
Headline: THEN AND NOW: The cast of the 'Harry Potter' films over 22 years later
Body: It's been 22 years since "Harry Potter and the Sorcerer's Stone" premiered. Here's what stars like Daniel Radcliffe and Rupert Grint are doing now.
Source: Business Insider
"""

# Input your API keys for https://newsapi.org/v2/everything", https://www.alphavantage.co/query, and TWILLO token/#

# Read stock data from CSV file (ensure "saved_stocks.csv" exists with appropriate columns)
df_stocks = pd.read_csv("saved_stocks.csv")

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"
PRICE_API_KEY = "YOUR ALPHA VANTAGE API KEY"
NEWS_API_KEY = "YOUR NEWS API KEY"

FROM = "YOUR TWILLO NUMBER"
TO = "YOUR PHONE NUMBER"
ACC_SID = "YOUR TWILLO ACCOUNT SID"
AUTH_TOKEN = "YOUR TWILLO AUTH TOKEN"

for index, row in df_stocks.iterrows():
    stock = row["Stock Symbol"]
    company = row["Company Name"]
    # API request parameters for stock price data
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": stock,
        "outputsize": "compact",
        "apikey": PRICE_API_KEY
    }
    # Send HTTP GET request to Alpha Vantage API
    response = requests.get(url=STOCK_ENDPOINT, params=params)

    # Handle potential errors (e.g., API request failures)
    response.raise_for_status()

    # Parse JSON response from API
    price_data = response.json()

    # Get today's date
    today = date.today()

    # Create an iterator to traverse the price data dictionary efficiently
    it = iter(price_data['Time Series (Daily)'].values())

    # Extract yesterday's and the day before yesterday's closing prices
    yester_price, before_yester_price = float(next(it)['4. close']), float(next(it)['4. close'])

    # Calculate percentage change in price
    perc_change = 100 * (yester_price - before_yester_price) / abs(before_yester_price)

    # API request parameters for news articles
    params2 = {
        "apiKey": NEWS_API_KEY,
        "q": company,
        "language": "en",
        "sortBy": "popularity"
    }

    # Send HTTP GET request to News API
    response2 = requests.get(url=NEWS_ENDPOINT, params=params2)

    # Handle potential errors (e.g., API request failures)
    response2.raise_for_status()

    # Parse JSON response from News API
    news_data = response2.json()['articles'][:3]
    print(news_data)
    print(perc_change)

    # Process and potentially send SMS notifications (adjust conditions based on your preferences)
    if perc_change > 1:
        if yester_price > before_yester_price:
            change = "🔺"
        else:
            change = "🔻"

        for x in news_data:
            source = x["source"]["name"]
            headline = x['title']
            body = x['description']

            # Create Twilio client using account SID and auth token
            client = Client(ACC_SID, AUTH_TOKEN)

            # Construct SMS message content
            message_text = f"{stock}: {change}{round(perc_change, 2)}%\n" \
                           f"Headline: {headline}\n" \
                           f"Body: {body}\n" \
                           f"Source: {source}"

            # Send SMS notification via Twilio (uncomment if desired)
            message = client.messages \
                .create(
                body=message_text,
                from_=FROM,
                to=TO
            )

            # Print message content for testing or logging purposes
            print(message_text)
            print(message.sid)
