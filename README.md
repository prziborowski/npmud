NpMud

A MUD written in python designed for modularity and simplicity
using websockets rather than traditional sockets.

The original goal is for learning some of the newer features of
python3 and designing a place to learn python for the users.
(The rooms provide information about python, its structure,
grammar, modules and examples).

Rooms can be expanded and modified easily in-game and generate
directional exits automatically.

Other modules are designed such that they can be added without
too many dependencies to slowly expand capabilities and not
require complicated refactoring.

Places where others can contribute:
1) Expand the python tutorial rooms, or expand game related rooms.
2) Expand capabilities/attributes of a user. Allow users to be
   looked at such that their description can be seen.
3) Add items that can be placed in rooms, in user's inventory
   or worn.
4) Allow other mobile creatures (NPC) that can wander around the
   map.
5) Ticks. A clock that allows stats to be restore, other modules
   to plug in such that mobile creatures can wander, items decay,
   a combat mobile can be plugged in.
6) Combat. Initially something basic to allow 1 or more user/mobile
   to fight.
7) Spells. Something to use up those MP stats. Offensive, defensive,
   attribute affecting (seeing invisible things).

Running a server should be as easy as downloading/installing python3.5,
pip install -r requirements.txt
python3 ws-serve.py

Running a client should be as easy as hosting the ws.html on that machine
or running
python3 ws-client.py
after downloading/installing python3.5 and installing the required modules
(pip install -r requirements.txt)

The project is maintained by: https://github.com/prziborowski

