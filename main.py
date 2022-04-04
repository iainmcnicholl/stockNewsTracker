import requests
import os
import datetime as dt
from twilio.rest import Client

# variables
STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc"

price_api_key = os.environ['ALPHAVANTAGE_API_KEY']
news_api_key = os.environ['NEWSAPI_API_KEY']
twilio_account_sid = os.environ['TWILIO_ACCOUNT_SID']
twilio_auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(twilio_account_sid, twilio_auth_token)


# functions
def get_trading_dates():
    # gets yesterday trading day and returns with previous trading day
    today = dt.datetime.today()
    if today.weekday() == 0:
        current_trading_day = today - dt.timedelta(days=3)
        last_trading_day = today - dt.timedelta(days=4)
    elif today.weekday() == 1:
        current_trading_day = today - dt.timedelta(days=1)
        last_trading_day = today - dt.timedelta(days=4)
    else:
        current_trading_day = today - dt.timedelta(days=1)
        last_trading_day = today - dt.timedelta(days=2)

    return str(current_trading_day)[0:10], str(last_trading_day)[0:10]


def get_price_data():
    # returns price data as json
    price_endpoint = 'https://www.alphavantage.co/query?'
    price_param = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': STOCK,
        'apikey': price_api_key
    }

    price_response = requests.get(price_endpoint, params=price_param)
    price_response.raise_for_status()

    return price_response.json()


def compare_prices(dates, price_data):
    # takes dates and price data and compares last two trading dates, if change >5% / -5% action
    current_trading_day_close = round(float(price_data['Time Series (Daily)'][dates[0]]['4. close']), 1)
    last_trading_day_close = round(float(price_data['Time Series (Daily)'][dates[1]]['4. close']), 1)
    percentage_change = (((current_trading_day_close - last_trading_day_close) / last_trading_day_close) * 100)
    if -2.5 >= percentage_change or percentage_change >= 2.5:
        return True, percentage_change


def get_news(trigger_news, dates):
    # returns price data as json
    if trigger_news:
        news_endpoint = 'https://newsapi.org/v2/everything?'
        news_param = {
            'apiKey': news_api_key,
            'q': COMPANY_NAME,
            'from': dates[1],
            'to': dates[0],
        }

        news_response = requests.get(news_endpoint, params=news_param)
        news_response.raise_for_status()

        three_article_dict = []
        for article in news_response.json()['articles'][0:3]:
            data_dict = {
                'title': article['title'],
                'description': article['description'],
            }
            three_article_dict.append(data_dict)

        for item in three_article_dict:
            print(f"Title: {item['title']}\nDescription: {item['description']}")

        return three_article_dict
    else:
        return False


def send_notification(news_items, percentage):
    if news_items == False:
        print("No movement!")
    else:
        for items in news_items:
            message = client.messages \
                .create(
                body=f"TSLA Change {percentage[1]}\nHeadline: {items['title']}\nBrief: {items['description']}",
                from_='++17652759137',
                to='+4407903890096'
            )
            print(message.sid)


send_notification(get_news(compare_prices(get_trading_dates(), get_price_data()), get_trading_dates()), compare_prices(get_trading_dates(), get_price_data()))
