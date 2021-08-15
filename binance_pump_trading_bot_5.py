# -*- coding: utf-8 -*-
"""
Created on Sat Mar 20 18:08:48 2021

@author: PAUL208
"""

#%% 1. Libraries

import config
import re
import numpy as np
import pandas as pd
from datetime import datetime
from datetime import timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from helper_functions import read_telegram3
from helper_functions import read_telegram2
import webbrowser
import threading
import time

#%% 2. Helper functions:

# Get the opening price:
def get_opening_price():
    
    global openPrice
    
    openPrice = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_30MINUTE)[499][1]
    openPrice = float(openPrice)
    #print('Open: ' + str(kline))
    
# Get the ask price:
def get_ask_price():
    
    global askPrice

    market = pd.DataFrame(client.get_orderbook_tickers())
    market = market.loc[market['symbol'] == symbol]
    askPrice = float(market['askPrice'].values[0])
    #quantity = round(trade_amount / askPrice,0) 
    
    #print('Ask: ' +  str(askPrice))

def open_web_exchange():
    
    global symbol
    
    url = 'https://www.binance.com/en/trade/' + asset + '_BTC?layout=pro' 
    webbrowser.register('firefox',
    	None,
    	webbrowser.BackgroundBrowser("C://Program Files//Mozilla Firefox//firefox.exe"))
    
    webPageOpen = webbrowser.get('firefox').open(url)
    
    return(webPageOpen)  


#%% 3. Instantiate a client

# Instantiate a Client:
client = Client(config.api_key, config.api_secret)


#%% 4. BTC pairs/ symbols

# Get all symbols: (IMPROVE: Screen out some cryptos, e.g. those with high MktCaps)

tickers = client.get_all_tickers()
df_tickers = pd.DataFrame(tickers)

# Get BTC pair symbols only
df_tickers = df_tickers[df_tickers['symbol'].str.endswith("BTC")]
symbols = df_tickers.symbol.unique() 

# Remove unecessary pairs
symbols = symbols[symbols != 'BTCBBTC'] # Exclude BTCBTC from this array!!!
symbols = symbols[symbols != 'BTCSTBTC']
symbols = symbols[symbols != 'WBTCBTC']
symbols = symbols[symbols != 'RENBTCBTC']
symbols = symbols[symbols != 'OMBTC']
symbols = symbols[symbols != 'NUBTC']
symbols = symbols[symbols != 'OSTBTC']
symbols = symbols[symbols != 'ETHBTC']
symbols = symbols[symbols != 'FORBTC']
symbols = symbols[symbols != 'LTCBTC']
symbols = symbols[symbols != 'DOGEBTC']
symbols = symbols[symbols != 'XRPBTC']
symbols = symbols[symbols != 'COMPBTC']
symbols = symbols[symbols != 'BNBBTC']
symbols = symbols[symbols != 'ADABTC']
symbols = symbols[symbols != 'XRPBTC']
symbols = symbols[symbols != 'PNTBTC']
symbols = symbols[symbols != 'DOTBTC']
symbols = symbols[symbols != 'BONDBTC']
symbols = symbols[symbols != 'BCHBTC']
symbols = symbols[symbols != 'SOLBTC']
symbols = symbols[symbols != 'LINKBTC']
symbols = symbols[symbols != 'LINKBTC']
symbols = symbols[symbols != 'THETABTC']
symbols = symbols[symbols != 'ETCBTC']
symbols = symbols[symbols != 'XLMBTC']
symbols = symbols[symbols != 'MATICBTC']
symbols = symbols[symbols != 'ICPBTC']
symbols = symbols[symbols != 'VETBTC']
symbols = symbols[symbols != 'FILBTC']
symbols = symbols[symbols != 'TRXBTC']
symbols = symbols[symbols != 'XMRBTC']
symbols = symbols[symbols != 'AAVEBTC']
symbols = symbols[symbols != 'EOSBTC']
symbols = symbols[symbols != 'FTTBTC']
symbols = symbols[symbols != 'CAKEBTC']
symbols = symbols[symbols != 'ALGOBTC']
symbols = symbols[symbols != 'MKRBTC']


'''
Take out the big market cap coins, like ETH.
'''

# Get the symbols for the cryptocurrencies under consideration
assets = np.array([re.sub("BTC","",x) for x  in symbols]) # assests

#%% 5. Symbol Information

info = client.get_exchange_info()

df_symbols = pd.DataFrame(info['symbols'])

temp = pd.DataFrame(df_symbols['filters'].to_list())
temp2 = pd.DataFrame(temp.iloc[:,0].to_list())
df_symbols = pd.concat([df_symbols,temp2],axis=1)

df_symbols = df_symbols[['symbol','status', 'baseAsset',
                         'baseAssetPrecision', 'quoteAsset',
                         'quotePrecision', 'quoteAssetPrecision',
                         'baseCommissionPrecision','quoteCommissionPrecision',
                         'icebergAllowed', 'ocoAllowed', 
                         'quoteOrderQtyMarketAllowed', 'isSpotTradingAllowed',
                         'isMarginTradingAllowed','minPrice',
                         'maxPrice', 'tickSize']]

df_symbols[['minPrice','maxPrice', 'tickSize']] = df_symbols[['minPrice','maxPrice', 'tickSize']].apply(pd.to_numeric)

df_symbols['tickSizePrecision'] =  abs(np.log10(df_symbols['tickSize'])).astype(int)

df_symbols = df_symbols[df_symbols['quoteAsset'] == 'BTC']
df_symbols = df_symbols[df_symbols['isMarginTradingAllowed'] == False]

df_symbols = df_symbols[df_symbols['baseAsset'] != 'GO']
df_symbols = df_symbols[df_symbols['baseAsset'] != 'BTCB']
df_symbols = df_symbols[df_symbols['baseAsset'] != 'BTCST']
df_symbols = df_symbols[df_symbols['baseAsset'] != 'WBTC']
df_symbols = df_symbols[df_symbols['baseAsset'] != 'RENBTC']
df_symbols = df_symbols[df_symbols['baseAsset'] != 'OM']
df_symbols = df_symbols[df_symbols['baseAsset'] != 'NU']
df_symbols = df_symbols[df_symbols['baseAsset'] != 'OST']
df_symbols = df_symbols[df_symbols['baseAsset'] != 'OM']
df_symbols = df_symbols[df_symbols['baseAsset'] != 'OM']

symbols = np.array(df_symbols['symbol'])
assets = np.array(df_symbols['baseAsset'])

# Save symbol information:

#%% 6. Inputs and Parameters

# Inputs:
trade_amount = 0.0002
target = 0.4
tp1 = 0.10
tp2 = 0.20
sl = 0.05
channel = 'https://t.me/s/wallstreetevents'

# Global variables:
inTrade = False # tradeExecuted, # Set indicator to show trade executed.
quantity = 0
askPrice = 0
openPrice = 0
balance = 0
symbol = ''
asset = ''
stopLimit1 = []
stopLimit2 = []
buy_limit = []
precision = 8
webPageOpen = False

# Threads:
t1 = threading.Thread(target=get_opening_price)
t2 = threading.Thread(target=get_ask_price)
t3 = threading.Thread(target=open_web_exchange)


#%% 7. Start Listening

# Reset:
channel = 'https://t.me/s/wallstreetevents'

trade_amount = 0.001
target = 0.15
stop_loss = 0.05

openPrice = 0 
askPrice = 0

asset = []
symbol = []

buy_limit = []
stop_limit = []

# Threads:
t1 = threading.Thread(target=get_opening_price)
t2 = threading.Thread(target=get_ask_price)
t3 = threading.Thread(target=open_web_exchange)


while len(asset) == 0:
    # Read the last Telegram message:
    text_msg = read_telegram3(channel) 
    
    # Make time pretty (Printing Server time)
    timestamp = datetime.now()
    #timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    print(timestamp)
    print(text_msg + '\n')
    
    # get the asset mentioned
    asset = [asset for asset in assets if(asset in text_msg)]

# get the biggest string in the list
asset = max(asset, key=len)

# Get symbol info:
symbol = asset + 'BTC'

# Get the precision of the coin
precision = df_symbols[df_symbols['symbol'] == symbol]['tickSizePrecision'].values[0]

# Get the Open price and Ask Price:
t1.start()
t2.start()

t1.join()
t2.join()

# Calculate Order Info:
pct_change = askPrice/openPrice - 1

if(target > pct_change):
    #IMPROVE: DON'T TRADE WHEN THE ASSET IS UP MORE THAN 20% IN THE LAST 4 HOURS.
    #IMPROVE: THE KLINES DATA CAN BE USED FOR THIS
    quantity = round(trade_amount / askPrice,0) # trade amount is position size.
    take_profit = target - pct_change
    
else:
    
    # don't trade:
    quantity = 0
    
    print('Price has already moved! \n')
# ----------------------------------------------------------------------------

# Place buy order:
try:
    
    buy_limit = client.order_limit_buy(
        symbol = symbol,
        quantity = quantity,
        price = '{:.{prec}f}'.format(askPrice * 1.0010, prec = precision),
        )

    # Message:
    print('We have bought {} {} coins at price {} \n'.format(quantity,
                                                      symbol,
                                                      format(askPrice,'.8f')))

except BinanceAPIException as e:
    print(e)
    
except BinanceOrderException as e:
    print(e)
    
# Place sell orders:
if (len(buy_limit) > 0):
    
    try:
        # Get balance:
        balance = client.get_asset_balance(asset=asset)
        balance = float(balance['free']) #IMPROVE!!!
    except:
        print("Error: Couldn't get the balance. Possibly no asset recognized.")
    
    
    try:
        
        stopLimit1 = client.create_oco_order(
            symbol = symbol,
            side = 'SELL',
            quantity = np.floor(balance),
            price = '{:.{prec}f}'.format(askPrice*(1 + take_profit), prec = precision), # Take profit
            stopPrice = '{:.{prec}f}'.format(askPrice*(1 - stop_loss) , prec = precision), # Stop Loss Trigger
            stopLimitPrice= '{:.{prec}f}'.format(askPrice*(1 - stop_loss), prec = precision), # Stop Loss
            stopLimitTimeInForce = 'GTC'
            )
        
        print('Take profit and stop loss have been placed!')
        
    except BinanceAPIException as e:
        print(e)
    
    except BinanceOrderException as e:
        print(e)


# Start get webpage thread:
t3.start()
        
    
#%%