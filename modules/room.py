"""
This modules is an implementation of "rooms" for the MUD.
It loads its state from a json file.
The keys are x, y, z coordinates of the spatial mapping.

Each room contains:
title - A one-line short description
desc - A description of the room
attribs - An array of properties the room can contain.
          e.g.: indoors, nosummon, nomagic, highregen.
exits - An array of directions a user can move to other rooms.
"""

import json
import os
from os.path import exists, join, dirname, realpath

ROOM_FILE = join(dirname(realpath(__file__)), 'rooms.json')
DST_ROOM_FILE = ROOM_FILE + '.bak'
room_map = {}
room_meta = {}


class Coordinate(object):
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __iter__(self):
        for v in [self.x, self.y, self.z]:
            yield v

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def move_coord(self, direction):
        if direction == 'west':
            self.x -= 1
        elif direction == 'east':
            self.x += 1
        elif direction == 'north':
            self.y += 1
        elif direction == 'south':
            self.y -= 1
        elif direction == 'up':
            self.z += 1
        elif direction == 'down':
            self.z -= 1
        else:
            raise Exception('Direction %s is not valid' % direction)


def opposite(direction):
    if direction == 'west':
        return 'the east'
    elif direction == 'east':
        return 'the west'
    elif direction == 'north':
        return 'the south'
    elif direction == 'south':
        return 'the north'
    elif direction == 'up':
        return 'below'
    elif direction == 'down':
        return 'above'
    raise Exception('unknown direction %s' % direction)


def direction(direction):
    if direction == 'west':
        return 'to the west'
    elif direction == 'east':
        return 'to the east'
    elif direction == 'north':
        return 'to the north'
    elif direction == 'south':
        return 'to the south'
    elif direction == 'up':
        return 'up'
    elif direction == 'down':
        return 'down'
    raise Exception('unknown direction %s' % direction)


def load():
    if not exists(ROOM_FILE):
        raise Exception('Failed to find %s' % ROOM_FILE)

    with open(ROOM_FILE, 'r') as f:
        global room_map
        room_map = json.load(f)

    if build_exits(room_map):
        save()
    build_meta(room_map)


def save():
    if exists(DST_ROOM_FILE):
        os.unlink(DST_ROOM_FILE)
    os.rename(ROOM_FILE, DST_ROOM_FILE)
    with open(ROOM_FILE, 'w') as f:
        # Use pretty-printing as it will be easier to diff.
        json.dump(room_map, f, indent=4, separators=(',', ': '))


def build_and_save():
    build_exits(room_map)
    save()


def build_meta(room_map):
    global room_meta
    for room_id in room_map.keys():
        room_meta[room_id] = {'users': []}


def build_exits(room_map):
    changed = False

    for room_id in room_map.keys():
        room = room_map[room_id]
        x, y, z = [int(x) for x in room_id.split(',')]

        for coord, direction in [((x, y + 1, z), 'north'),
                                 ((x, y - 1, z), 'south'),
                                 ((x - 1, y, z), 'west'),
                                 ((x + 1, y, z), 'east'),
                                 ((x, y, z + 1), 'up'),
                                 ((x, y, z - 1), 'down')]:
            exists = room_exists(get_room_id(*coord))
            if exists and direction not in room['exits']:
                changed = True
                room['exits'].append(direction)
    return changed


def get_room_id(x, y, z):
    return '%d,%d,%d' % (x, y, z)


def room_exists(room_id):
    global room_map
    return room_id in room_map


def get_room(coord):
    global room_map
    room_id = get_room_id(coord.x, coord.y, coord.z)
    if room_id not in room_map:
        raise Exception('Room not found')
    return room_map[room_id]


def add_room(room_id):
    global room_map
    assert not room_exists(room_id)
    room_map[room_id] = {'title': '', 'desc': '', 'exits': [], 'attribs': []}


def add_user(user):
    global room_meta
    room_id = get_room_id(user._coord.x, user._coord.y, user._coord.z)
    room_meta[room_id]['users'].append(user)


def add_god_user(user):
    room_id = get_room_id(*user._coord)
    if not room_exists(room_id):
        global room_meta
        add_room(room_id)
        room_meta[room_id] = {'users': []}
    add_user(user)


def remove_user(user):
    global room_meta
    room_id = get_room_id(*user._coord)
    room_meta[room_id]['users'].remove(user)


def can_move_user(user, direction):
    room = get_room(user._coord)
    return direction in room['exits']


def move_user(user, direction):
    remove_user(user)
    user._coord.move_coord(direction)
    add_user(user)


def get_users(coord):
    global room_meta
    room_id = get_room_id(*coord)
    return room_meta[room_id]['users']
