from . import room

import sqlite3
from hashlib import sha256


def get_connection():
    return sqlite3.connect('users.db')


def create_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Users
                 (nickname TEXT PRIMARY KEY NOT NULL,
                  password TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS UsersCoord
                 (nickname TEXT PRIMARY KEY NOT NULL,
                  x INT NOT NULL, y INT NOT NULL, z INT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS UsersAttrib
                 (nickname TEXT, name TEXT, value TEXT,
                  PRIMARY KEY(nickname, name))''')
    conn.commit()
    c.close()
    conn.close()


def load_user(name, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM Users WHERE nickname=:n AND password=:p',
              {'n': name, 'p': sha256(password.encode()).hexdigest()})
    result = c.fetchone()[0]
    c.close()
    conn.close()
    return result > 0


def load_user_attrib(name):
    conn = get_connection()
    c = conn.cursor()
    attrib = {}
    for result in c.execute('SELECT name, value FROM UsersAttrib '
                            'WHERE nickname=:n', {'n': name}):
        try:
            intresult = int(result[1])
            attrib[result[0]] = intresult
        except ValueError:
            attrib[result[0]] = result[1]

    c.close()
    conn.close()
    return attrib


def add_user_attrib(user, name, value):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO UsersAttrib (nickname, name, value)
                 VALUES (:user, :name, :value)''',
              {'user': user, 'name': name, 'value': value})
    conn.commit()
    c.close()
    conn.close()


def load_user_coord(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT x, y, z FROM UsersCoord WHERE nickname=:n', {'n': name})
    result = c.fetchone()
    if result is None:
        x, y, z = 0, 0, 0
    else:
        x, y, z = result[0:3]
    c.close()
    conn.close()
    return room.Coordinate(x, y, z)


def save_user_coord(name, x, y, z):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO UsersCoord (nickname, x, y, z)
                 VALUES (:n, :x, :y, :z) ''',
              {'n': name, 'x': x, 'y': y, 'z': z})
    conn.commit()
    c.close()
    conn.close()


def save_user(name, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO Users (nickname, password) VALUES (:n, :p)''',
              {'n': name, 'p': sha256(password.encode()).hexdigest()})
    conn.commit()

    c.execute('''SELECT count(*) FROM Users''')
    result = c.fetchone()[0]
    c.close()
    conn.close()
    if result == 1:
        add_user_attrib(name, 'god', '1')
        add_user_attrib(name, 'builder', '1')


def exists(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM Users WHERE nickname=:n', {'n': name})
    result = c.fetchone()[0]
    c.close()
    conn.close()
    return result > 0
