import orjson
import aiohttp
import asyncio
import discord

client = discord.Client()
token = ""
#target_channel = 

async def connect_bitmex():
    url = r"wss://www.bitmex.com/realtime?subscribe=instrument:XBTUSD,trade:XBTUSD"
    session = aiohttp.ClientSession(json_serialize=orjson.dumps)
    ws = await session.ws_connect(url=url,heartbeat=5)
    connect_msg = await ws.receive_json(loads=orjson.loads)
    print(connect_msg)
    success_msg = await ws.receive_json(loads=orjson.loads)
    print(success_msg)
    success_msg = await ws.receive_json(loads=orjson.loads)
    print(success_msg)
    #success_msg = await ws.receive_json(loads=orjson.loads)
    #print(success_msg)
    return ws

def extract_oi(resp):
    if "openInterest" in resp["data"][0].keys():
        oi = resp["data"][0]["openInterest"]
        return oi
    return -1

async def get_following_oi(ws, tradelist):
    while True:
        resp = await ws.receive_json(loads=orjson.loads)
        if resp["table"] == "trade" and resp["action"] == "insert":
            total_size = 0
            for entry in resp["data"]:
                total_size += entry["size"]
            if total_size >= 50000:
                slip = abs(float(resp["data"][0]["price"]) - float(resp["data"][-1]["price"]))
                tradelist.append((resp["data"][0]["price"],resp["data"][-1]["price"], total_size, resp["data"][0]["side"],slip))
        
        if resp["table"] == "instrument" and resp["action"] == "update":
            oi = extract_oi(resp)
            if oi != -1: return oi,tradelist
        

async def send_results(trade_info, prev_oi, following_oi, slippage,tradelist):
    channel = client.get_channel(726040524141887558)  
    
    if (len(tradelist) == 1) and (trade_info[2] > 150000):
    #if len(tradelist) == 1:
        if (trade_info[3] == 'Sell'):
            if float(prev_oi) < float(following_oi):
                await channel.send("""```diff\n-%s %s Slippage: %s First price: %s || Last price: %s\nTrade Opened Position```""" %(trade_info[3],format(trade_info[2],','),slippage,format(trade_info[0],','),format(trade_info[1],',')))
                  
            else:
                await channel.send("""```diff\n-%s %s Slippage: %s First price: %s || Last price: %s\nTrade Closed Position```""" %(trade_info[3],format(trade_info[2],','),slippage,format(trade_info[0],','),format(trade_info[1],',')))
                
        if (trade_info[3] == 'Buy'):
            if float(prev_oi) < float(following_oi):
                await channel.send("""```diff\n+%s %s Slippage: %s First price: %s || Last price: %s\nTrade Opened Position```""" %(trade_info[3],format(trade_info[2],','),slippage,format(trade_info[0],','),format(trade_info[1],',')))
                
            else:
                await channel.send("""```diff\n+%s %s Slippage: %s First price: %s || Last price: %s\nTrade Closed Position```""" %(trade_info[3],format(trade_info[2],','),slippage,format(trade_info[0],','),format(trade_info[1],',')))
                
    if len(tradelist) > 1:
        for o in tradelist:
            if (o[3] == 'Sell'):
                await channel.send("""```diff\n-%s %s Slippage: %s First price: %s || Last price: %s```""" %(o[3],format(o[2],','),o[4],format(o[0],','),format(o[1],',')))
                
            if (o[3] == 'Buy'):
                await channel.send("""```diff\n+%s %s Slippage: %s First price: %s || Last price: %s```""" %(o[3],format(o[2],','),o[4],format(o[0],','),format(o[1],',')))
                
        if (following_oi > prev_oi):
            await channel.send("""```diff\n+Increase OI %s First price: %s || Last price: %s```""" %(format((int(following_oi) - int(prev_oi)),','),format(tradelist[0][0],','),format(tradelist[-1][1],',')))
            
        if (following_oi < prev_oi):
            await channel.send("""```diff\n-Decrease OI %s First price: %s || Last price: %s```""" %(format((int(following_oi) - int(prev_oi)),','),format(tradelist[0][0],','),format(tradelist[-1][1],',')))
            
        
                 
            


async def parse_data():
    ws = await connect_bitmex()
    prev_oi = None
    following_oi = None
    while True:
        tradelist = []
        resp = await ws.receive_json(loads=orjson.loads)
        #print(resp)
        if resp["table"] == "instrument" and resp["action"] == "update":
            oi = extract_oi(resp)
            if oi != -1: prev_oi = oi 
            continue
                
        if resp["table"] == "trade" and resp["action"] == "insert":
            total_size = 0
            for entry in resp["data"]:
                total_size += entry["size"]
            #edit min trade size here    
            if total_size >= 500000:
                trade_info = (resp["data"][0]["price"],resp["data"][-1]["price"], total_size, resp["data"][0]["side"])
                slippage = abs(float(resp["data"][0]["price"]) - float(resp["data"][-1]["price"]))
                tradelist.append((resp["data"][0]["price"],resp["data"][-1]["price"], total_size, resp["data"][0]["side"],slippage))
                if prev_oi == None: print("previous oi has not been collected from stream yet")
                following_oi,tradelist = await get_following_oi(ws,tradelist)
                await send_results(trade_info, prev_oi, following_oi, slippage,tradelist)
                prev_oi = following_oi
                            

async def on_ready():
    print("connected")

async def disc():
    await client.wait_until_ready()
    while not client.is_closed():
        while True:
            try:
                await parse_data()
            except TypeError:
                continue

client.loop.create_task(disc())
client.run(token)
        



