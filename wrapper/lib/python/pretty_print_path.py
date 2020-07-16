"""A silly module which can pretty print sys.path

"""

from sys import path
from pprint import pprint

__all__ = ('pretty_print_path',)

def pretty_print_path():
    pprint(path)
