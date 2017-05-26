from . import commands
from . import lang
from . import room
from . import users_db

import asyncio
from queue import Queue
import logging
import os

logger = logging.getLogger('npmud')

motd = ""
if os.path.exists('motd.txt'):
    with open('motd.txt', 'r') as f:
        motd = f.read()


class UserStats(object):
    def __init__(self):
        self.hp = [100, 100]
        self.mp = [100, 100]
        self.sp = [100, 100]


class UserAttribs(object):
    def __init__(self, initial_values):
        self.__dict__ = initial_values


class UserBase(object):
    def __init__(self, websocket):
        self._ws = websocket
        self._name = None
        self._message_queue = Queue()
        self._stats = UserStats()
        self._position = 'standing'
        self._is_loaded = False

    def restore(self):
        self._prompt = 'HP:{hp}/{hp_max} MP:{mp}/{mp_max} SP:{sp}/{sp_max}> '
        if self.is_god():  # Gods don't care about mortal stats.
            self._prompt = '{x},{y},{z}> '

    def is_god(self):
        return getattr(self._attrib, 'god', False)

    def is_builder(self):
        return getattr(self._attrib, 'builder', False)

    def set_name(self, name):
        self._name = name

    def get_name(self):
        return self._name

    def save(self):
        if self._is_loaded:
            users_db.save_user_coord(self.get_name(), self._coord.x,
                                     self._coord.y, self._coord.z)

    def load(self, password):
        if not users_db.load_user(self.get_name(), password):
            return False
        # Now we have established the user/pass is correct, we can load
        # the other data
        self._coord = users_db.load_user_coord(self.get_name())
        self._attrib = UserAttribs(users_db.load_user_attrib(self.get_name()))
        self.restore()
        self._is_loaded = True
        return True

    def create(self, password):
        users_db.save_user(self.get_name(), password)
        self._attrib = UserAttribs(users_db.load_user_attrib(self.get_name()))
        self.restore()
        self._is_loaded = True


class User(UserBase):
    def __init__(self, websocket):
        super(User, self).__init__(websocket)

    async def process_input(self, input_):
        await commands.process(self, input_)

    async def say(self, fromUser, message):
        perspective = 2 if self == fromUser else 3
        self.add_message(lang.form(perspective, "{person} {say} '{message}'.",
                                   person=lang.PERSON,
                                   user=fromUser.get_name(),
                                   say=lang.SAY, message=message))

    async def broadcast(self, fromUser, message):
        perspective = 2 if self == fromUser else 3
        self.add_message(lang.form(perspective,
                                   "{person} {broadcast} '{message}'.",
                                   person=lang.PERSON,
                                   user=fromUser.get_name(),
                                   broadcast=lang.BROADCAST, message=message))
    async def get_message(self):
        while self._message_queue.empty():
            await asyncio.sleep(0.1)
        return self._message_queue.get(), self._message_queue.empty()

    def add_message(self, message):
        self._message_queue.put(message)

    async def send_welcome(self):
        logger.debug('Connection received from {}'.format(
                     self._ws.remote_address[0]))
        await self._ws.send(motd)
        await self._ws.send('Please tell me your name: ')
        response = await self._ws.recv()
        self.set_name(response)
        if users_db.exists(response):
            await self._ws.send('Enter your password: ')
            password = await self._ws.recv()
            if not self.load(password):
                logging.info("Password mismatch for {}".format(
                             self.get_name()))
                await self._ws.close()
                return False
        else:
            await self._ws.send('Welcome new user. Please give me a password '
                                'to remember you by: ')
            first_password = await self._ws.recv()
            await self._ws.send('Once more to confirm: ')
            second_password = await self._ws.recv()
            if first_password != second_password:
                await self._ws.send("Sorry they didn't match. "
                                    "Try reconnecting.")
                await self._ws.close()
                return False
            self.create(first_password)
            self._coord = room.Coordinate()
        room.add_user(self)
        await send_enter_game(self)
        return True

    async def send(self, message):
        try:
            await self._ws.send(message)
        except websockets.exceptions.ConnectionClosed:
            await self.exit()

    async def prompt(self):
        try:
            prompt = self._prompt.format(hp=self._stats.hp[0],
                                         hp_max=self._stats.hp[1],
                                         mp=self._stats.mp[0],
                                         mp_max=self._stats.mp[1],
                                         sp=self._stats.sp[0],
                                         sp_max=self._stats.sp[1],
                                         x=self._coord.x,
                                         y=self._coord.y,
                                         z=self._coord.z)
            await self._ws.send(prompt)
        except websockets.exceptions.ConnectionClosed:
            await self.exit()

    async def send_part(self, direction):
        people = [x for x in room.get_users(self._coord) if x is not self]
        if len(people) > 0:
            await asyncio.wait([u.send('You see {} walk {}.'.format(
                                       self.get_name(),
                                       room.direction(direction)))
                                for u in people])

    async def send_enter(self, direction):
        people = [x for x in room.get_users(self._coord) if x is not self]
        if len(people) > 0:
            await asyncio.wait([u.send('You see {} arrive from {}.'.format(
                                       self.get_name(),
                                       room.opposite(direction)))
                                for u in people])

    async def exit(self):
        if self not in all():
            return  # already removed

        self.save()
        remove(self)
        room.remove_user(self)
        if len(all()) > 0:
            await asyncio.wait(
                [u.send('{} has left the game.'.format(self.get_name()))
                 for u in all()])
        logger.info('User {} has left.'.format(self.get_name()))
        await self._ws.close()


async def send_enter_game(user):
    userNames = [u.get_name() for u in all() if u.get_name() is not None]
    send('Greetings {}!'.format(user.get_name()))
    logger.info('{} joined.'.format(user.get_name()))
    logger.info('Users present: {}'.format(', '.join(userNames)))
    user.add_message('Currently present: {}'.format(', '.join(userNames)))

    await user.process_input('look')


users = set()


def remove(user):
    users.remove(user)


def add(user):
    users.add(user)


def all():
    return users


def send(message):
    [u.add_message(message) for u in users]
