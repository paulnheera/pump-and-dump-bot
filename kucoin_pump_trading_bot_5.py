# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 20:11:03 2021

@author: PAUL208
"""

#%% 1. Load libraries
import re
from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import time
from configparser import ConfigParser
from kucoin.client import Market , Trade, User
from kucoin.exceptions import KucoinAPIException , LimitOrderException
from helper_functions import read_telegram3
import webbrowser
import threading
import feather
from configparser import ConfigParser

#%% 2. API Connections
exchange = 'kucoin'
config = ConfigParser()
config.read('config.cfg')
api_key = config.get(exchange, 'api_key')
api_secret = config.get(exchange, 'api_secret')
api_passphrase = config.get(exchange, 'api_passphrase')

clientMarket = Market(url='https://api.kucoin.com')
clientTrade = Trade(key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=False, url='')
clientUser = User(key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=False, url='')

#%% 3. Helper functions

def round_down(num,divisor):
    
    x = np.floor(num/divisor) * divisor
    
    x = round(x, -np.log10(divisor).astype(int) )
    
    return(x)

def get_opening_price():
    
    global openPrice
    
    start_time = datetime.now() - timedelta(minutes=15)
    start_time = format(start_time.timestamp(),'.0f')
    klines = clientMarket.get_kline(symbol, '5min',startAt = start_time)
    openPrice = klines[0][1]
    openPrice = float(openPrice)
      
def get_ask_price():
    
    global symbol
    global askPrice
    
    ticker = clientMarket.get_ticker(symbol)
    askPrice = float(ticker['bestAsk'])
     
def open_web_exchange():
    
    global symbol
    
    url = 'https://trade.kucoin.com/' + symbol
    webbrowser.register('firefox',
    	None,
    	webbrowser.BackgroundBrowser("C://Program Files//Mozilla Firefox//firefox.exe"))
    
    webPageOpen = webbrowser.get('firefox').open(url)
    
    return(webPageOpen)

def start_stop_loss():
    
    global symbol
    global market_order
    global askPrice
    global bid
    global stop_loss
    
    while len(market_order) == 0:
       
        bid = float(clientMarket.get_ticker(symbol)['bestBid'])
        
        print('Price movement: {}%'.format(format((bid/askPrice - 1)*100, '.2f')))
              
        if ((bid/askPrice)-1 < -stop_loss):
            try:
                # Market order
                market_order = clientTrade.create_market_order(
                    symbol = symbol,
                    side = 'sell',
                    size = format(round_down(balance, minSize))
                    )
            except KucoinAPIException as e:
    
                print(e)
            except LimitOrderException as e:
    
                print(e)
                
def get_trades():
    
    global symbol
    global trades
    
    for i in range(10):
        # get trades from kucoin
        curr_trades = clientMarket.get_trade_histories(symbol)
        trades.extend(curr_trades)
        print('Got trades!')
        
        time.sleep(2)
    
#%% 4. Get symbols

# Get all available pairs
res = clientMarket.get_symbol_list()
df_Symbols = pd.DataFrame(res)

# Filter for where the quote currency is USDT
df_Symbols = df_Symbols[df_Symbols['quoteCurrency'] == 'USDT']
# Exclude coins where margin is allowed
df_Symbols = df_Symbols[df_Symbols['isMarginEnabled'] == False] # Exclude coins where margin is allowed:
# Get unique symbols
df_Symbols = df_Symbols.drop_duplicates()

# Convert columns to numeric
df_Symbols[['baseMinSize', 'baseMaxSize', 'quoteMaxSize', 'baseIncrement', 
            'quoteIncrement', 'priceIncrement', 'priceLimitRate']] = \
df_Symbols[['baseMinSize', 'baseMaxSize', 'quoteMaxSize', 'baseIncrement', 'quoteIncrement', 'priceIncrement', 'priceLimitRate']].apply(pd.to_numeric)

# Quote precision
df_Symbols['precision'] = abs(np.log10(df_Symbols['priceIncrement'])).astype(int)

# Symbols
symbols = df_Symbols['symbol'].unique()

### FILTER OUT UNECCESSARY SYMBOLS LIKE R-USDT
symbols = symbols[symbols != 'R-USDT']
symbols = symbols[symbols != 'GO-USDT']
symbols = symbols[symbols != 'BTC-USDT']
symbols = symbols[symbols != 'ETH-USDT']
symbols = symbols[symbols != 'ONE-USDT']
symbols = symbols[symbols != 'USDN-USDT']
symbols = symbols[symbols != 'USDJ-USDT']
symbols = symbols[symbols != 'BUY-USDT']
symbols = symbols[symbols != 'USDC-USDT']
symbols = symbols[symbols != 'SDT-USDT']
symbols = symbols[symbols != 'WIN-USDT']
symbols = symbols[symbols != 'NU-USDT']
symbols = symbols[symbols != 'T-USDT']

# Assets
assets = np.array([re.sub("-USDT","",x) for x in symbols])

#%% 5. Inputs and Global variables

# Inputs:
trade_amount = 10   # <--- UPADATE!!!
target = 0.20
take_profit1 = 0.1
take_profit2 = 0.2
stop_loss = 0.1

channel = 'https://t.me/s/channel_de_pump'

# Declare trade variables as global variables
# Global variables
inTrade = False # tradeExecuted , Set indicator to show trade executed:
quantity = 0
askPrice = 0
openPrice = 0
target = 0
balance = 0
symbol = ''
asset = ''
test = 0
stopLimit1 = []
stopLimit2 = []
buy_limit = []
precision = 0  
minSize = 0
bid = 0
webPageOpen = False

# Threads:
t1 = threading.Thread(target=get_opening_price)
t2 = threading.Thread(target=get_ask_price)
t3 = threading.Thread(target=open_web_exchange)
t4 = threading.Thread(target=start_stop_loss)
t5 = threading.Thread(target=get_trades)


#%% 6. Start Listening:

# Reset:
trade_amount = 10
target = 0.30
stop_loss = 0.05

openPrice = 0 
askPrice = 0

asset = []
symbol = []

market_order = []
stop_limit = []
buy_limit = []

trades = []

# Threads:
t1 = threading.Thread(target=get_opening_price)
t2 = threading.Thread(target=get_ask_price)
t3 = threading.Thread(target=open_web_exchange)
t4 = threading.Thread(target=start_stop_loss)
t5 = threading.Thread(target=get_trades)

# Listening to Telegram
while len(asset) == 0:
    # Read the last Telegram message:
    text_msg = read_telegram3(channel) 
    
    # Make time pretty (Printing Server time)
    timestamp = datetime.now()
    #timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    print(timestamp)
    print(text_msg + '\n')
    
    # get asset mentioned
    asset = [asset for asset in assets if(asset in text_msg)]

# get the biggest string in the list
asset = max(asset, key=len)

# Get symbol info:
symbol = asset + '-USDT'
precision = df_Symbols[df_Symbols['symbol'] == symbol]['precision'].values[0]
tick = df_Symbols[df_Symbols['symbol'] == symbol]['priceIncrement'].values[0]
minSize = df_Symbols[df_Symbols['symbol'] == symbol]['baseMinSize'].values[0]

# Get the Open price and Ask Price:
t1.start()
t2.start()
#t3.start()

t1.join()
t2.join()

# Calculate Order Info:
pct_change = askPrice/openPrice - 1

if(target > pct_change):
    #IMPROVE: DON'T TRADE WHEN THE ASSET IS UP MORE THAN 20% IN THE LAST 4 HOURS.
    #IMPROVE: THE KLINES DATA CAN BE USED FOR THIS
    # Determine the quantity to trade
    quantity = round_down(trade_amount / askPrice, minSize) # trade amount is position size.
    take_profit = target - pct_change
    
else:
    # don't trade:
    quantity = 0
    print('Price has moved past the target!')
    
# ----
    
# Optimise on where to set the buy limit.
# Also Optimise the market request. Currently takes about a second.

# Price change in the last 24hrs
# changeRate = float(client.get_24hr_stats(symbol)['changeRate'])

# Get the price 4hours ago to assess pre-pump
changeRate = 0 # Used to check that there is no pre-pump.
    
    
# Place a limit buy order: ---------------------------------------------------
# Only by if balance is zero (or some percentage)
# Only by if price is less than [opening price + 5%]
try:
    if(changeRate < 0.4): # Make sure that the coin is not pre-pumped.
        buy_limit = clientTrade.create_limit_order(
            symbol = symbol,
            side = 'buy',
            size = format(quantity),
            price = '{:.{prec}f}'.format(askPrice + 2*tick, prec = precision)
            )
        print('We have bought {} {} coins at price {} \n'.format(quantity, symbol, format(askPrice,'.8f')))
    else:
        print("Trade not allowed. Pre-pumped coin. \n")
except KucoinAPIException as e:
    # error handling goes here
    print(e)
except LimitOrderException as e:
    # error handling goes here
    print(e)
    
# Open webpage: --------------------------------------------------------------
t3.start()
    
# Place sell orders: ----------------------------------------------------------
if (len(buy_limit) > 0):
# if the buy order got placed:
    # Get balance:     
    try:
        df_accounts = pd.DataFrame(clientUser.get_account_list())
        balance = df_accounts[df_accounts['currency'] == asset]['available'].values[0]
        balance = float(balance)
    except:
        print("Error: Couldn't get the balance. Possibly no asset recognized.")
    # Place stop limit - Take Profit:
    try:
        stop_limit = clientTrade.create_limit_order(
            symbol = symbol,
            side = 'sell',
            size = format(round_down(balance, minSize)),
            price = '{:.{prec}f}'.format(askPrice * (1 + take_profit), prec = precision)
            )
        print("The take profit has been placed! \n")
    except KucoinAPIException as e:
        print(e)
        # If Filter failure: MIN_NOTIONAL then set a stoploss with entire balance!!!
    except LimitOrderException as e:
        print(e)
       
    # Start stoploss process:   
    t4.start()
                
# Start process to download trades:
t5.start()              
        
#%% 7. Save trades data

# convert to dataframe
df_trades = pd.DataFrame(trades)

# convert to numeric:
df_trades[['sequence','price','size','time']] = \
    df_trades[['sequence','price','size','time']].apply(pd.to_numeric)

# convert time:
df_trades['time'] = pd.to_datetime(df_trades['time'])

# add symbol name:
df_trades.insert(0,'symbol',symbol)

# file name:
filename = f'{symbol} - {datetime.now().date()}'

# save:
df_trades.to_csv('kucoin data/' + filename + '.csv')

feather.write_dataframe(df_trades,'kucoin data/' +  filename + '.feather')


#%%