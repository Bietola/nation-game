import sys
import subprocess
from pathlib import Path
import os
from inspect import getsourcefile
import time
from funcy import compose
from result import Err, Ok
from functools import partial, reduce, wraps
import operator as op

SRC_PATH = Path(os.path.abspath(getsourcefile(lambda:0))).parent

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def shell(*args):
    return subprocess.check_output(*args, shell=True)

def wait_until_connected(delay, trace=False):
    import urllib.request

    def try_connect(host='http://google.com'):
        try:
            urllib.request.urlopen(host) #Python 3.x
            return True
        except:
            return False

    while True:
        if try_connect():
            print('Connection successful!')
            return
        else:
            print(f'Connection failed... checking again in {delay}s')
            time.sleep(delay)

def indices(pred, l):
    return [index for index, v in enumerate(l) if pred(v)]

def all_prefix_matches(validator, to_validate):
    return map(
        lambda i: to_validate[i],
        indices(
            partial(op.eq, True),
            list(map(
                compose(
                    all,
                    partial(map, partial(reduce, op.eq))),
                map(
                    compose(list, partial(zip, validator)),
                    to_validate)))))

def unique_prefix_match(validator, to_validate):
    prefix_matches = list(all_prefix_matches(validator, to_validate))

    if len(prefix_matches) == 0:
        return Err('ERR: None')

    elif len(prefix_matches) > 1:
        return Err('ERR: Ambiguous')

    else:
        return Ok(prefix_matches[0])

def awaitify(sync_func):
    """Wrap a synchronous callable to allow ``await``'ing it"""
    @wraps(sync_func)
    async def async_func(*args, **kwargs):
        return sync_func(*args, **kwargs)
    return async_func