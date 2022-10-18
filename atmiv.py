import requests
import json
import math
import random
import datetime
import re
import operator
import time

deribitproducts = json.loads(requests.get("https://www.deribit.com/api/v2/public/get_instruments?currency=BTC").text)

#get options chain
options_list = []
for instruments in deribitproducts['result']:
    if instruments['kind'] == 'option' and instruments['settlement_period'] == 'month':
        options_list.append(instruments['instrument_name'])
        
options_expiry = []
for dates in options_list:
    if dates[0:11] not in options_expiry:

        options_expiry.append(dates[0:11])
        
counter = 0
for expires in options_expiry:

    if expires[-1] == '-':
        options_expiry[counter] = options_expiry[counter][:-1]
    counter += 1

option_dict = {}

datelist = []
for e in options_expiry:

    request_time = datetime.datetime.strptime(e,'BTC-%d%b%y')

    datelist.append((e,request_time))

datelist.sort(key=lambda x:x[1])

sort_options_instruments = []

sort_options_instruments = []
for instruments in options_list:
        if datelist[0][0] in instruments:
            sort_options_instruments.append((datelist[0][0],datelist[0][1],instruments,instruments[-1],int(re.findall(r'\d+', instruments[11:])[0])))
            
list1 = sorted(sort_options_instruments,key=operator.itemgetter(1,3,4))

#find atm iv
#as u trend towards expiry u know the delta must go towards either 0 or 1, .5 is midpoint 
#and so u find smallest delta difference to .5

best_delta_diff = 1
atm_option = ''
atm_iv = 0
for e in list1:
    option_ticker = json.loads(requests.get(("https://www.deribit.com/api/v2//public/ticker?instrument_name=%s")%e[2]).text)
    delta_diff = abs(abs(option_ticker['result']['greeks']['delta']) - .5)
    if delta_diff < best_delta_diff:
        best_delta_diff = delta_diff
        atm_option = option_ticker['result']['instrument_name']
        atm_iv = option_ticker['result']['mark_iv']
    time.sleep(.1)