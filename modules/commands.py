from . import room
from . import users

import asyncio
import re

def get_command_from_input(user, input_):
    command = [c for c in COMMAND_LIST if c[0].startswith(input_)]
    if len(command) == 0 and (user.is_god() or user.is_builder()):
        command = [c for c in GOD_COMMAND_LIST
                   if c[0].startswith(input_)]
    if len(command) == 0:
        return None
    else:
        return command[0]

async def process(user, input_):
    input_ = input_.strip()
    userCommand, *remainder = re.split('\s+', input_, 1)

    if userCommand == '':
        user.add_message('')
        return
    command = get_command_from_input(user, userCommand)
    if not command:
        user.add_message('Unknown command: {}'.format(userCommand))
        return

    name, func, *_ = command
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


async def help_command(user, remainder, **kwargs):
    if len(remainder) == 0:
        command_list = '\n'.join([n[0] for n in COMMAND_LIST])
        user.add_message('What would like to know more about?\n'
                         'Type help <command>\n'
                         '{}'.format(command_list))
        return
    command = get_command_from_input(user, remainder[0])
    if not command:
        user.add_message("I can't help you with {}".format(remainder[0]))
        return
    help_message = command[2]
    user.add_message(help_message)


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
        user.process_input('')
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
   ("'", say, "Say something to the room you are in"),
   ('broadcast', broadcast, "Broadcast a message to everyone"),
   #   'cast',
   #   'close',
   ('down', move, "Move down"),
   ('east', move, "Move east"),
   #   'emote',
   ('exits', exits, "List the visible exits from this room"),
   ('help', help_command, "Get help about particular commands"),
   ('look', look, "Look at the room details"),
   #   'laugh',
   ('north', move, "Move north"),
   #   'open',
   ('quit', quit, "Quit the game"),
   ('south', move, "Move south"),
   ('say', say, "Say something to the room you are in"),
   ('sit', sit, "Sit down and rest"),
   #   'shout',
   #   'scream',
   ('stand', stand, "Stand up from sitting position"),
   ('up', move, "Move up"),
   ('west', move, "Move west"),
]

GOD_COMMAND_LIST = [
   ('goto', god_goto, "Goto a map coordinate, whether the room exists or not"),
   ('set', god_set, "Set a property. 'title' for title of room, " \
                    "'desc' for room description"),
   #   'summon',
]
