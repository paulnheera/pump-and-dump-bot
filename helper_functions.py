# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 20:19:23 2021

@author: PAUL208
"""

#%% 1. Libraries
import requests
from bs4 import BeautifulSoup
import lxml

#%% Read telegram

def read_telegram(channel):
    
    response = requests.get(channel)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('div')
    messages =[link.text for link in links]
    text_msg = messages[-3]
    #text_msg = 'The coin we have picked to pump today is :  #PIVXPIVX is looking perfect for a pump right now , our target is 1000%'
    
    return(text_msg)

#%%
    
def read_telegram2(channel):
    
    response = requests.get(channel)
    soup = BeautifulSoup(response.content, 'html.parser')
    msg_boxes = soup.find_all('div', class_ = 'tgme_widget_message_text js-message_text')
    text_msg = msg_boxes[-1].text
    
    return(text_msg)

#%% Read Telegram function, version 3

def read_telegram3(channel):
    
    '''
    This functions extracts and returns the last message in a telegram channel.
    Arguments:
        channel (string): Telegram channel URL
    '''
    
    response = requests.get(channel)
    soup = BeautifulSoup(response.content, 'lxml')
    msg_boxes = soup.find_all('div', class_ = 'tgme_widget_message_text js-message_text')
    text_msg = msg_boxes[-1].text
    
    return(text_msg)

#%% Get Binance trades
    
import numpy as np
import pandas as pd
from datetime import datetime
from datetime import timezone
from binance.client import Client

import  pytz

# Instantiate a Client:
client = Client()

# Inputs:
# symbol
# start_time - has to be datetime object, with utc timezone
# end_time

symbol = 'MTHBTC'
start_time = '2021-06-27 16:58'
end_time = '2021-06-27 17:03'

start_time = datetime.strptime(start_time , '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
end_time = datetime.strptime(end_time , '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)


def get_binance_trades(symbol, start_time, end_time):
    

    # time in as string:
    start_time = datetime.strptime(start_time , '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
    end_time = datetime.strptime(end_time , '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
    
    # prepare inputs
    start_str = start_time.strftime("%d %B, %Y %H:%M")
    df_trades  = pd.DataFrame(columns = ['a','p','q','f','l','T','m','M'])
    
    # Get the trades aggregator
    agg_trades = client.aggregate_trade_iter(symbol = symbol, start_str = start_str)
    
    # Download the trades
    for trade in agg_trades:
    
        df_temp = pd.DataFrame(trade, index=[0])
        
        df_trades = df_trades.append(df_temp, ignore_index=True)
                
        trade_time = pd.to_datetime(df_temp['T'], unit='ms')[0]
        trade_time = trade_time.to_pydatetime()
        
        # make datetime aware of the timezone
        trade_time = pytz.utc.localize(trade_time)
        
        # stop loop
        if end_time < trade_time:
            break
    
    # Convert to dataframe and format
    df_trades['T'] = pd.to_datetime(df_trades['T'], unit='ms')
    
    df_trades.columns = ['Seller Order Id', 'Price', 'Quantity', 'Ignore', 'Ignore', 'Time', 'Sell', 'Ignore' ]
    df_trades['Side'] = np.where(df_trades['Sell'] == True, 'Sell', 'Buy')
    df_trades = df_trades[['Seller Order Id', 'Price', 'Quantity','Time', 'Side']]
    df_trades[['Seller Order Id','Price','Quantity']] =  \
        df_trades[['Seller Order Id','Price','Quantity']].apply(pd.to_numeric)
        
    # output the dataframe
    return df_trades

#%%
