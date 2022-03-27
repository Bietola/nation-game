import sys
import subprocess
from pathlib import Path
import os
from inspect import getsourcefile
import time

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
