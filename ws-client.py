#!/usr/bin/env python3
import asyncio
import sys
import websockets

async def consumer(message):
    print("\n{}".format(message), end=' ')


async def consumer_handler(websocket):
    while True:
        try:
            message = await websocket.recv()
            await consumer(message)
        except:
            break


async def producer(loop):
    return await loop.run_in_executor(None, sys.stdin.readline)


async def producer_handler(websocket):
    while True:
        message = await producer(asyncio.get_event_loop())
        await websocket.send(message.rstrip())


async def client(ip):
    async with websockets.connect('ws://{ip}:4000'.format(ip=ip)) as websocket:
        consumer_task = asyncio.ensure_future(consumer_handler(websocket))
        producer_task = asyncio.ensure_future(producer_handler(websocket))

        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()


def main(args):
    if len(args) < 1:
        print("Please provide a remote server to connect to.")
        return
    asyncio.get_event_loop().run_until_complete(client(args[0]))


if __name__ == '__main__':
    main(sys.argv[1:])
