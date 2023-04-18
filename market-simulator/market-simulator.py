import asyncio
import ujson
import time
import sys 
import pandas as pd
import os
import warnings
import cProfile, pstats

from gate_ws import Configuration, Connection, WebSocketResponse
from gate_ws.spot import SpotPublicTradeChannel, SpotOrderBookChannel, SpotOrderBookUpdateChannel, SpotBookTickerChannel

warnings.filterwarnings('ignore')

best_global = -1
limit_orders = []

all_limit_orders = []
all_market_orders = []
settings = {
    "channel_name": "BTC_USD",
    "depth": "20",
    "update_rate": "1000ms"
    }

TIMEOUT = 10 #secs

NUM_OF_SNAPSHOTS = 5
curr_snapshot = 0
orders = []

def print_message(conn: Connection, response: WebSocketResponse):
    global curr_snapshot
    global NUM_OF_SNAPSHOTS
    global orders
    if response.error:
        print('error returned: ', response.error)
        conn.close()
        return
    
    data = response.result
    if list(data.keys())[0] != "status":
        orders.append(data)
        curr_snapshot += 1
    
    if curr_snapshot >= NUM_OF_SNAPSHOTS:
        conn.close()
        return
        
async def generate_orderbook():
    filename = "orderbook.json"
    
    conn = Connection(Configuration())
    
    channel = SpotOrderBookChannel(conn, print_message)
    
    channel.subscribe([settings["channel_name"], settings["depth"], settings["update_rate"]])

    await conn.run()
    
    channel.unsubscribe([settings["channel_name"], settings["depth"], settings["update_rate"]])
    
    with open(filename, "w") as file:
        data = ujson.dumps(orders, indent=4)
        # print(data)
        file.write(data)
        
def clean_orderbook():
    df = pd.read_json("orderbook.json")
    
    df2 = pd.DataFrame(df)

    df2[[f'bid_{i}' for i in range(20)]] = pd.DataFrame(df2.bids.tolist(), index= df2.index)
    df2[[f'ask_{i}' for i in range(20)]] = pd.DataFrame(df2.asks.tolist(), index= df2.index)
    
    for i in range(20):
        df2[[f'bid_{i}_px', f"bid_{i}_qty"]] = pd.DataFrame(df2[f"bid_{i}"].tolist(), index= df2.index).apply(pd.to_numeric, errors = 'coerce')
        df2[[f'ask_{i}_px', f"ask_{i}_qty"]] = pd.DataFrame(df2[f"ask_{i}"].tolist(), index= df2.index).apply(pd.to_numeric, errors = 'coerce')
    
    df2.drop(columns = [f'bid_{i}' for i in range(20)]+[f'ask_{i}' for i in range(20)]+["bids","asks", "lastUpdateId"], axis=1, inplace = True)

    return df2
    
def place_market_order(side = "buy", price = 10000, qty = 1):
    asyncio.run(generate_orderbook())
    df = clean_orderbook()
    
    order = [side, price, qty]
    all_market_orders.append(order)
    
    dollar_value = float(price)
    
    price = []

    for row in df.to_dict(orient="records"):
        
        side = "ask" if side == "buy" else "bid"
            
        total_price = 0
        total_qty = 0

        for i in range(20):
            if(total_price < dollar_value):
                total_price += row[f"{side}_{i}_px"] * row[f"{side}_{i}_qty"]
                total_qty += row[f"{side}_{i}_qty"]
                last = str(i)
                
#         print(f"Total {order_type}: {total_price}")
        
        if total_price >= dollar_value:
            extra = total_price - dollar_value
            total_qty = total_qty - extra / row[f"{side}_{last}_px"]
        else:
            extra = dollar_value - total_price
            total_qty = total_qty + extra / row[f"{side}_{last}_px"]

#         print(total_price)
        
        avg_price = dollar_value / total_qty
        price.append(avg_price)
    
    print(df)
    
    print(price)


def check(conn: Connection, response: WebSocketResponse):
    global best_global
    global limit_orders
#     print(limit_orders)
    side = limit_orders[0][0]
    price = float(limit_orders[0][1])
    qty = float(limit_orders[0][2])
    
    if response.error:
        print('error returned: ', response.error)
        conn.close()
        return
    
    data = response.result
    
    if list(data.keys())[0] != "status":
        best_local = float(data[f"{side}"])
        if best_local != best_global: #check if value of best bid/ask price has changed
            best_global = best_local
            print(f"order_price: {price}, best_{side}_local = {best_local}")
            if side == "b":
                if price < best_local:
                    print(f"Order executed at price: {best_local}")
                    order = [side, price, qty]
                    all_limit_orders.append(order)
                    limit_orders.clear()
                    conn.close()
                    return
            if side == "a":
                if price > best_local:
                    print(f"Order executed at price: {best_local}")
                    order = [side, price, qty]
                    all_limit_orders.append(order)
                    limit_orders.clear()
                    conn.close()
                    return
            
        
async def order_stream():
    global settings
    # channel_name = "BTC_USD"
    # depth = "5"
    # update_rate = "1000ms"
    
    conn = Connection(Configuration())
    # time_start = time.perf_counter()
    channel = SpotBookTickerChannel(conn, check)
    # time_end = time.perf_counter()
    # print(f"{time_end - time_start}, {TIMEOUT}")
    channel.subscribe([settings["channel_name"]])
    
    await conn.run()

#Assumption
#Once best bid / ask price crosses the limit price, we assume the entire quantity is executed
async def place_limit_order(side = "sell", price = 20000, qty = 1):
    side = "a" if side == "buy" else "b"
    limit_orders.append([side, price, qty])
    await order_stream()

def print_start_msg():
    print("Welcome to the Exchange Simulator!")
    print()
    print("Enter a number to start")
    print()
    print("1: Place orders")
    print("2: Order history")
    print("3: Settings")
    print("4: Exit")
    print()

def print_order_msg():
    print("Which type of order would you like to place?")
    print()
    print("1: Market order")
    print("2: Limit order")
    print("3: Back")
    print()
    
def print_limit_order_msg():
    print("Place Limit Order")
    print()

def print_market_order_msg():
    print("Place Market Order")
    print()
    
def print_back_msg():
    print()
    input("Press [ENTER] to continue")

def take_input():
    type = input("side (buy/sell): ")
    price = input("price: ")
    qty = input("qty: ")
    print()
    
    return type, price, qty

def print_invalid_msg():
    print()
    print("Please enter a valid number!")
    print()
    input("Press [ENTER] to try again")
    
def print_limit_history_msg():
    global all_limit_orders
    print("Limit Order History")
    print()
    
    if len(all_limit_orders) == 0:
        print("No successful limit orders")
    
    for i in range(len(all_limit_orders)):
        print(f"{i + 1}. {all_limit_orders[i]}")

    print()
    
def print_market_history_msg():
    global all_market_orders
    print("Market Order History")
    print()
    
    if len(all_market_orders) == 0:
        print("No successful market orders")
    
    for i in range(len(all_market_orders)):
        print(f"{i + 1}. {all_market_orders[i]}") 
    
    print()

def print_settings_msg():
    print("Settings")
    print()
    print("1: View current settings")
    print("2: Change settings")
    print("3: Back")
    print()

def print_settings_view_msg():
    global settings
    print("Current Settings")
    print()
    print(f"Channel name: {settings['channel_name']}")
    print(f"Depth: {settings['depth']}")
    print(f"Update rate: {settings['update_rate']}")
    print()

def change_settings():
    global settings
    
    channel_name = input("Channel name (default: BTC_USD): ")
    depth = input("Depth (default: 5): ")
    update_rate = input("Update rate (default: 1000ms): ")
    
    settings["channel_name"] = channel_name
    settings["depth"] = depth
    settings["update_rate"] = update_rate
    
def print_settings_change_msg():
    print("Change Settings")
    print()
    
   
STATES = ["home", "select_order", "market_order", "limit_order", "history", "settings", "view_settings", "update_settings"]
curr_state = "home"

def main():
    global curr_state
    global STATES
    
    os.system('cls' if os.name == 'nt' else 'clear')
    
    if curr_state == "home":
        print_start_msg()

        cmd = input("Enter a number: ")
        if cmd == "1":
            curr_state = STATES[1] #select_order
            main()
        elif cmd == "2":
            curr_state = STATES[4] #history
            main()
        elif cmd == "3":
            curr_state = STATES[5] #settings
            main()
        elif cmd == "4":
            print()
            print("Thank you for using the exchange simulator!")
            # exit(0)
            return
        else:
            print_invalid_msg()
            main()
            
    elif curr_state == "select_order":
        print_order_msg()
        
        order_type = input("Enter a number: ")
        
        if order_type == "1":
            curr_state = STATES[2] #market_order
            main()
            # place_market_order()
        elif order_type == "2":
            curr_state = STATES[3] #limit_order
            main()
        elif order_type == "3":
            curr_state = STATES[0] #home
            main()
        else:
            print_invalid_msg()
            main()
            
    elif curr_state == "market_order":
        print_market_order_msg()
        
        type, price, qty = take_input()
        
        place_market_order(type, price, qty)
        
        print_back_msg()
        
        curr_state = STATES[0] #home
        main()
        
    elif curr_state == "limit_order":
        print_limit_order_msg()
        
        type, price, qty = take_input()
        
        asyncio.run(place_limit_order(type, price, qty))
        
        print_back_msg()
        
        curr_state = STATES[0] #home
        main()
    
    elif curr_state == "history":
        print_limit_history_msg()
        print_market_history_msg()
        print_back_msg()
        
        curr_state = STATES[0] #home
        main()
        
    elif curr_state == "settings":
        print_settings_msg()
        settings_action = input("Enter a number: ")
        
        if settings_action == "1":
            curr_state = STATES[6] #view_settings
            main()
        elif settings_action == "2":
            curr_state = STATES[7] #update_settings
            main()
        elif settings_action == "3":
            curr_state = STATES[0] #home
            main()
        else:
            print_invalid_msg()
            main()
    
    elif curr_state == "view_settings":
        print_settings_view_msg()
        print_back_msg()
        curr_state = STATES[5] #settings
        main()
    
    elif curr_state == "update_settings":
        print_settings_change_msg()
        change_settings()
        print_back_msg()
        curr_state = STATES[5] #settings
        main()      
        
    else:
        print_invalid_msg()
        main()
        
        
if __name__ == "__main__":
    # profiler = cProfile.Profile()
    # profiler.enable()
    # main()
    # profiler.disable()
    # stats = pstats.Stats(profiler).sort_stats('tottime')
    # stats.print_stats(10)
    # cProfile.run('main()')
    # main()
    main()