#!/usr/bin/env python3

# Module loading will be more dynamic in the future
# but for now just import what we need.
from modules import room
from modules import users
from modules import users_db

import asyncio
import logging
import logging.handlers
import re
import websockets

logger = logging.getLogger('npmud')


def setup_logging(logger):
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    fh = logging.handlers.RotatingFileHandler('npmud.log',
                                              maxBytes=1024 * 1024,
                                              backupCount=20)
    formatting = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(formatting)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

setup_logging(logger)


"""
The command list should be an array with callback methods.
It wouldn't be in a dictionary/hash because this ordering is
important for which commands have a higher priority.

"""


def consumer(message):
    logger.debug('Recv: {}'.format(message))


async def consumer_handler(user):
    while True:
        try:
            message = await user._ws.recv()
            await user.process_input(message)
            consumer(message)
        except websockets.exceptions.ConnectionClosed:
            await user.exit()


async def producer_handler(user):
    while True:
        message, empty = await user.get_message()
        await user.send(message)
        if empty:
            await user.prompt()


async def handler(websocket, path):
    newuser = users.User(websocket)
    if not await newuser.send_welcome():
        return
    users.add(newuser)

    try:
        consumer_task = asyncio.ensure_future(consumer_handler(newuser))
        producer_task = asyncio.ensure_future(producer_handler(newuser))

        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()
    finally:
        try:  # Try to safely logout user
            await newuser.exit()
        except:
            pass


users_db.create_table()
room.load()
start_server = websockets.serve(handler, '0.0.0.0', 4000)

loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
try:
    loop.run_forever()
except KeyboardInterrupt:
    logger.info('Shutting down server.')
    if len(users.all()) > 0:
        [u.save() for u in users.all()]
    # Safely save all progress
