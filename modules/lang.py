PERSON = ['I', 'you', '{user}']
SAY = ['say', 'say', 'says']
SHOUT = ['shout', 'shout', 'shouts']
BROADCAST = ['broadcast', 'broadcast', 'broadcasts']


def form(perspective, formatting, **kwargs):
    for key, value in kwargs.items():
        if isinstance(value, list):
            kwargs[key] = value[perspective - 1]
    first_process = formatting.format(**kwargs)
    return first_process.format(**kwargs).capitalize()
