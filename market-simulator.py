import asyncio

from gate_ws import Configuration, Connection, WebSocketResponse
from gate_ws.spot import SpotPublicTradeChannel, SpotOrderBookChannel, SpotOrderBookUpdateChannel


# define your callback function on message received
def print_message(conn: Connection, response: WebSocketResponse):
    if response.error:
        print('error returned: ', response.error)
        conn.close()
        return
    print(response.result)


async def main():
    # initialize default connection, which connects to spot WebSocket V4
    # it is recommended to use one conn to initialize multiple channels
    conn = Connection(Configuration())

    # subscribe to any channel you are interested into, with the callback function
    channel = SpotOrderBookChannel(conn, print_message)
    channel.subscribe(["BTC_USDT", "20", "1000ms"])

    # start the client
    await conn.run()


if __name__ == '__main__':
   loop = asyncio.get_event_loop()
   loop.run_until_complete(main())
   loop.close()