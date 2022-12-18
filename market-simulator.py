import asyncio
import ujson
import time
import sys

from gate_ws import Configuration, Connection, WebSocketResponse
from gate_ws.spot import SpotPublicTradeChannel, SpotOrderBookChannel, SpotOrderBookUpdateChannel

NUM_OF_SNAPSHOTS = 5
curr_snapshot = 0
orders = []

# define your callback function on message received
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
        
async def main():
    channel_name = sys.argv[1] if len(sys.argv) > 1 else "BTC_USD"
    depth = sys.argv[2] if len(sys.argv) > 2 else "20"
    update_rate = sys.argv[3] if len(sys.argv) > 3 else "1000ms"
    
    filename = "orderbook.json"
    #initialize default connection, which connects to spot WebSocket V4
    # it is recommended to use one conn to initialize multiple channels
    conn = Connection(Configuration())

    # subscribe to any channel you are interested into, with the callback function
    channel = SpotOrderBookChannel(conn, print_message)
    
    # start_time = time.perf_counter()
    
    channel.subscribe([channel_name, depth, update_rate])
    
    # end_time = time.perf_counter()
    
    # print(f"Time: {end_time - start_time}")

    # start the client
    await conn.run()
    
    with open(filename, "w") as file:
        data = ujson.dumps(orders, indent=4)
        print(data)
        file.write(data)

if __name__ == '__main__':
    start_time = time.perf_counter()
    asyncio.run(main())
    end_time = time.perf_counter()
    print(f"Time: {end_time - start_time}")