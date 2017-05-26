from . import room
from . import users

import asyncio
import re


async def process(user, input_):
    input_ = input_.strip()
    userCommand, *remainder = re.split('\s+', input_, 1)
    if userCommand == '':
        user.add_message('')
        return
    command = [c for c in COMMAND_LIST if c[0].startswith(userCommand)]
    if len(command) == 0:
        if user.is_god() or user.is_builder():
            command = [c for c in GOD_COMMAND_LIST
                       if c[0].startswith(userCommand)]
            if len(command) == 0:
                user.add_message('Unknown command: {}'.format(userCommand))
                return
        else:
            user.add_message('Unknown command: {}'.format(userCommand))
            return
    name, func = command[0]  # Pick the first one
    await func(user=user, rawinput=input_, name=name, remainder=remainder)


async def quit(user, **kwargs):
    await user.exit()


async def say(user, remainder, **kwargs):
    if len(remainder) == 0:
        user.add_message('Say what?')
    else:
        await send_say_to_room(user, remainder[0])


async def broadcast(user, remainder, **kwargs):
    if len(remainder) == 0:
        user.add_message('Broadcast what?')
    else:
        await send_broadcast(user, remainder[0])


async def look(user, **kwargs):
    user_room = room.get_room(user._coord)
    user.add_message('{}\n\n{}\n'.format(user_room['title'],
                                         user_room['desc']))
    people = [x for x in room.get_users(user._coord) if x is not user]
    for person in people:
        user.add_message('You see {} {} here.'.format(person.get_name(),
                                                      person._position))
    await user.process_input('exits')


async def move(user, name, **kwargs):
    if user._position != 'standing':
        user.add_message("You can't move while {}.".format(user._position))
    elif room.can_move_user(user, name):
        await user.send_part(name)
        room.move_user(user, name)
        await user.send_enter(name)
        await user.process_input('look')
    else:
        user.add_message("You can't go {}.".format(name))


async def sit(user, **kwargs):
    if user._position == 'sitting':
        user.add_message('You are already {}'.format(user._position))
    else:
        user._position = 'sitting'
        user.add_message('You sit down.')


async def stand(user, **kwargs):
    if user._position == 'standing':
        user.add_message('You are already {}'.format(user._position))
    else:
        user._position = 'standing'
        user.add_message('You stand up.')


async def exits(user, **kwargs):
    user_room = room.get_room(user._coord)
    user.add_message('Exits:\n{}'.format(', '.join(user_room['exits'])))


async def god_goto(user, remainder, **kwargs):
    coords = re.split('\s+', remainder[0])
    if len(coords) < 3:
        user.add_message("I can't take you there.")
        return
    room.remove_user(user)
    user._coord.x, user._coord.y, user._coord.z, *_ = [int(x) for x in coords]
    room.add_god_user(user)
    await user.process_input('look')


async def god_set(user, remainder, **kwargs):
    if len(remainder) == 0:
        user.add_message('Set what?')
        return
    prop, *remainder = re.split('\s+', remainder[0], 1)
    if user.is_builder() and prop == 'title':
        user_room = room.get_room(user._coord)
        user_room['title'] = remainder[0]
        room.build_and_save()
    elif user.is_builder() and prop == 'desc':
        # Keep running until we get a line only containing 'end'.
        user.add_message("OK, go ahead. Stop with a line containing 'end'.")
        room_desc = ''
        while True:
            response = await user._ws.recv()
            if response == 'end':
                break
            room_desc += response + '\n'
        user_room = room.get_room(user._coord)
        user_room['desc'] = room_desc
        room.build_and_save()
        await user.process_input('look')


async def send_say_to_room(fromUser, message):
    await asyncio.wait([u.say(fromUser, message)
                       for u in users.all() if u._coord == fromUser._coord])


async def send_broadcast(fromUser, message):
    await asyncio.wait([u.broadcast(fromUser, message) for u in users.all()])


COMMAND_LIST = [
   ("'", say),
   ('broadcast', broadcast),
   #   'cast',
   #   'close',
   ('down', move),
   ('east', move),
   #   'emote',
   ('exits', exits),
   #   'help',
   ('look', look),
   #   'laugh',
   ('north', move),
   #   'open',
   ('quit', quit),
   ('south', move),
   ('say', say),
   ('sit', sit),
   #   'shout',
   #   'scream',
   ('stand', stand),
   ('up', move),
   ('west', move),
]

GOD_COMMAND_LIST = [
   ('goto', god_goto),
   ('set', god_set),
   #   'summon',
]
