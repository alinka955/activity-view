# -*- coding: utf-8 -*-
"""
This file contains methods and classes that activity-view relies on.
"""

import typing
from   typing import *

###
# Credits
###
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2022, University of Richmond'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'Alina Enikeeva'
__email__ = 'alina.enikeeva@richmond.edu'
__status__ = 'in progress'
__license__ = 'MIT'


###
# Standard imports, starting with os and sys
###
min_py = (3, 8)
import enum
import os
import sys
if sys.version_info < min_py:
    print(f"This program requires Python {min_py[0]}.{min_py[1]}, or higher.")
    sys.exit(os.EX_SOFTWARE)

###
# Other standard distro imports
###
import argparse
import contextlib
import getpass
import shlex
import subprocess
import logging
from   logging.handlers import RotatingFileHandler
import pathlib
import math
import pprint
from   functools import reduce



mynetid = getpass.getuser()

###
# imports that are a part of this project
###
from wrapper import trap

###
# global objects
###
verbose = False

############# scaling code begin ##########

@trap
def row(used:int, max_avail:int, scale:int=80, x:str="X", _:str="_", ends=('[', ']')) -> str:
    """
    used -- quantity to be filled with x.
    max_avail -- set of which used is a subset.
    scale -- if scale < max_avail, then used and max_avail are divided by scale.
    x -- the char used to show in-use-ness.
    _ -- the char used to show not-in-use-ness.
    ends -- decorators for start/finish.
    """
    try:
        used=int(used)
        max_avail=int(max_avail)
        scale=int(scale)
    except:
        raise Exception("numeric quantities are required")
    
    if not len(x) * len(_) * scale * max_avail:
        raise Exception("Cannot use zero length delimiters")

    if used < 0 or max_avail < 0 or scale < 0:
        raise Exception("quantities must be non-negative")

    used = max_avail if used > max_avail else used

    if scale < max_avail:
        used = round(used * scale / max_avail)
    else:
        scale = max_avail

    xes = used*x
    _s  = (scale-used)*_

    return f"{ends[0]}{xes}{_s}{ends[1]}"


    

############## scaling code end ################

################# mapper and file utilities code begin #################
@trap
def draw_map() -> dict:

    scaling_values = {
        384000 : 25,
        768000 : 50,
        1536000 : 100
        }

    data = SeekINFO()
    memory_map = []
    core_map = []
   
    # We don't need the header row here is an example line:
    #
    # spdr12 424105 768000 up 52 12/40/0/52

    for line in ( _ for _ in data.stdout.split('\n')[1:] if _ ):
        node, free, total, status, true_cores, cores = line.split()
        cores = cores.split('/')
        used = int(total) - int(free)
        scale=scaling_values[int(total)]
        memory_map.append(f"{node} {row(used, total, scale)}")
        core_map.append(f"{node} {row(cores[1], true_cores)}")

    return {"memory":memory_map, "cores":core_map}

@trap
def SeekINFO() -> tuple:
    cmd = 'sinfo -o "%n %e %m %t %c %C"'
    data = SloppyTree(dorunrun(cmd, return_datatype=dict))
    
    if not data.OK:
        verbose and print(f"sinfo failed: {data.code=}")
        return os.EX_DATAERR

    verbose and print(data.stdout)
    return data

 
def read_whitespace_file(filename:str) -> tuple:
    """
    This is a generator that returns the whitespace delimited tokens 
    in a text file, one token at a time.
    """
    if not filename: return tuple()

    if not os.path.isfile(filename):
        sys.stderr.write(f"{filename} cannot be found.")
        return os.EX_NOINPUT

    f = open(filename)
    yield from (" ".join(f.read().split('\n'))).split()
    
################## mapper and file utilities code end ##############


################### dorunrun code utility begin #####################

@trap
def dorunrun(command:Union[str, list],
    timeout:int=None,
    verbose:bool=False,
    quiet:bool=False,
    return_datatype:type=bool,
    ) -> Union[str, bool, int, dict]:
    """
    A wrapper around (almost) all the complexities of running child 
        processes.
    command -- a string, or a list of strings, that constitute the
        commonsense definition of the command to be attemped. 
    timeout -- generally, we don't
    verbose -- do we want some narrative to stderr?
    quiet -- overrides verbose, shell, etc. 
    return_datatype -- this argument corresponds to the item 
        the caller wants returned. It can be one of these values.

            bool : True if the subprocess exited with code 0.
            int  : the exit code itself.
            str  : the stdout of the child process.
            dict : everything as a dict of key-value pairs.

    returns -- a value corresponding to the requested info.
    """

    # If return_datatype is not in the list, use dict. Note 
    # that the next statement covers None, as well.
    return_datatype = dict if return_datatype not in (int, str, bool) else return_datatype

    # Let's convert all the arguments to str and relieve the caller
    # of that responsibility.
    if isinstance(command, (list, tuple)):
        command = [str(_) for _ in command]
        shell = False
    elif isinstance(command, str):
        command = shlex.split(command)
        shell = False
    else:
        raise Exception(f"Bad argument type to dorunrun: {command=}")

    if verbose: sys.stderr.write(f"{command=}\n")

    try:
        result = subprocess.run(command, 
            timeout=timeout, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            shell=False)

        code = result.returncode
        b_code = code == 0
        i_code = code
        s = result.stdout[:-1] if result.stdout.endswith('\n') else result.stdout
        e = result.stderr[:-1] if result.stderr.endswith('\n') else result.stderr

        if return_datatype is int:
            return i_code
        elif return_datatype is str:
            return s
        elif return_datatype is bool:
            return b_code
        else:
            return {"OK":b_code, 
                    "code":i_code, 
                    "name":ExitCode(i_code).name, 
                    "stdout":s, 
                    "stderr":e}
        
    except subprocess.TimeoutExpired as e:
        raise Exception(f"Process exceeded time limit at {timeout} seconds.")    

    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")




class FakingIt(enum.EnumMeta):

    def __contains__(self, something:object) -> bool:
        """
        Normally ... the "in" operator checks if something is in
        an instance of the container. We want to check if a value
        is one of the IntEnum class's members.
        """
        try:
            self(something)
        except ValueError:
            return False

        return True


class ExitCode(enum.IntEnum, metaclass=FakingIt):
    """
    This is a comprehensive list of exit codes in Linux, and it 
    includes four utility functions. Suppose x is an integer:

        x in ExitCode     # is x a valid value?
        x.OK              # Workaround: enums all evaluate to True, even if they are zero.
        x.is_signal       # True if the value is a "killed by Linux signal"
        x.signal          # Which signal, or zero.
    """

    @property
    def OK(self) -> bool:
        return self is ExitCode.SUCCESS

    @property
    def is_signal(self) -> bool:
        return ExitCode.KILLEDBYMAX > self > ExitCode.KILLEDBYSIGNAL

    @property 
    def signal(self) -> int:
        return self % ExitCode.KILLEDBYSIGNAL if self.is_signal else 0


    # All was well.
    SUCCESS = os.EX_OK

    # It just did not work. No info provided.
    GENERAL = 1

    # BASH builtin error (e.g. basename)
    BUILTIN = 2
    
############### dorunrun utility code end ###################


############### loger utility code begin ####################
def piddly(s:str) -> str:
    """
    A text wrapper for logging the output of multithreaded and
    multiprocessing programs.

    Example: 

        logger=URLogger()
        logger.info(piddly(msg))
    """
    return f": {os.getppid()} <- {os.getpid()} : {s}"


class URLogger: pass

class URLogger:
    __slots__ = {
        'logfile': 'the logfile associated with this object',
        'formatter': 'format string for the logging records.', 
        'level': 'level of the logging object',
        'rotator': 'using the built-in log rotation system',
        'thelogger': 'the logging object this class wraps'
        }

    __values__ = (
        None,
        logging.Formatter('#%(levelname)-8s [%(asctime)s] (%(process)d) %(module)s: %(message)s'),
        logging.WARNING,
        None,
        None)

    __defaults__ = dict(zip(__slots__.keys(), __values__))

    def __init__(self, **kwargs) -> None:

        # Set the defaults.
        for k, v in URLogger.__defaults__.items():
            setattr(self, k, v)

        # Override the defaults if needed.
        for k, v in kwargs.items(): 
            if k in URLogger.__slots__:
                setattr(self, k, v)
        
        try:
            if self.logfile is None:
                self.logfile=os.path.join(os.getcwd(), "thisprog.log")
            pathlib.Path(self.logfile).touch(mode=0o644, exist_ok=True)

        except Exception as e:
            sys.stderr.write(f"Cannot create or open {self.logfile}. {e}\n")
            raise e from None

        self.rotator = RotatingFileHandler(self.logfile, maxBytes=1<<24, backupCount=2)
            
        self.rotator.setLevel(self.level)
        self.rotator.setFormatter(self.formatter)

        # setting up logger with handlers
        self.thelogger = logging.getLogger('URLogger')
        self.thelogger.setLevel(self.level)
        self.thelogger.addHandler(self.rotator)


    ###
    # These properties provide an interface to the built-in
    # logging functions as if the class member, self.thelogger,
    # were exposed. 
    ###
    @property
    def debug(self) -> object:
        return self.thelogger.debug

    @property
    def info(self) -> object:
        return self.thelogger.info

    @property
    def warning(self) -> object:
        return self.thelogger.warning

    @property
    def error(self) -> object:
        return self.thelogger.error

    @property
    def critical(self) -> object:
        return self.thelogger.critical


    ###
    # Tinker with the object model a little bit.
    ###
    def __str__(self) -> str:
        """ return the name of the logfile. """
        return self.logfile


    def __int__(self) -> int:
        """ return the current level of logging. """
        return self.level


    def __call__(self, level:int) -> URLogger:
        """
        reset the level of logging, and return 'self' so that
        syntax like this is possible:

            mylogger(logging.INFO).info('a new message.')
        """
        self.level = level
        self.rotator.setLevel(self.level)
        self.thelogger.setLevel(self.level)
        return self 

############ logger utility code ends ###################

########### sloppytree (tree) utility code begin #######


class SloppyDict: pass

def sloppy(o:object) -> SloppyDict:
    """
    Returns a dictionary.
    """
    return o if isinstance(o, SloppyDict) else SloppyDict(o)


def deepsloppy(o:dict) -> Union[SloppyDict, object]:
    """
    Multi level slop.
    """
    if isinstance(o, dict): 
        o = SloppyDict(o)
        for k, v in o.items():
            o[k] = deepsloppy(v)

    elif isinstance(o, list):
        for i, _ in enumerate(o):
            o[i] = deepsloppy(_)

    else:
        pass

    return o


class SloppyDict(dict):
    """
    Make a dict into an object for notational convenience.
    """
    def __getattr__(self, k:str) -> object:
        """
        Gets the value of the key in the dictionary.
        """
        if k in self: return self[k]
        raise AttributeError(f"No element named {k}")

    def __setattr__(self, k:str, v:object) -> None:
        """
        Sets the value to the key in the dictionary.
        """
        self[k] = v

    def __delattr__(self, k:str) -> None:
        """
        Deletes the key in the dictionary.
        """
        if k in self: del self[k]
        else: raise AttributeError(f"No element named {k}")

    def reorder(self, some_keys:list=[], self_assign:bool=True) -> SloppyDict:
        """
        Sorts the keys in the dictionary.
        """
        new_data = SloppyDict()
        unmoved_keys = sorted(list(self.keys()))

        for k in some_keys:
            try:
                new_data[k] = self[k]
                unmoved_keys.remove(k)
            except KeyError as e:
                pass

        for k in unmoved_keys:
            new_data[k] = self[k]

        if self_assign: 
            self = new_data
            return self
        else:
            return copy.deepcopy(new_data)       



class SloppyTree: pass
class SloppyTree(dict):
    """
    Like SloppyDict() only worse -- much worse.
    """
    def __getattr__(self, k:str) -> object:
        """
        Retrieve the element, or implicity call the over-ridden 
        __missing__ method, and make a new one.
        """
        return self[k]

    def __delattr__(self, k:str) -> None:
        """
        Remove it if we can.
        """
        if k in self: del self[k]


    def __ilshift__(self, keys:Union[list, tuple]) -> SloppyTree:
        """
        Create a large number of sibling keys from a list.
        """
        for k in keys:
            self[k] = SloppyTree()
        return self


    def __invert__(self) -> int: 
        """
        return the number of paths from the root node to the leaves,
        ignoring the nodes along the way.
        """
        return sum(1 for _ in (i for i in self.leaves()))


    def __iter__(self) -> object:
        """
        NOTE: dict.__iter__ only sees keys, but SloppyTree.__iter__
        also sees the leaves.
        """
        return self.traverse


    def __len__(self) -> int:
        """
        return the number of nodes/branches.
        """
        return sum(1 for _ in (i for i in self.traverse(False)))



    def __missing__(self, k:str) -> object:
        """
        If we reference an element that doesn't exist, we create it,
        and assign a SloppyTree to its value.
        """
        self[k] = SloppyTree()
        return self[k]



    def __setattr__(self, k:str, v:object) -> None:
        """
        Assign the value as expected.
        """
        self[k] = v


    def __str__(self) -> str:
        return self.printable

    ###
    # All objects derived from dict need these functions if they
    # are to be pickled or otherwise examined internally.
    ###
    def __getstate__(self): return self.__dict__

    def __setstate__(self, d): self.__dict__.update(d)

    def leaves(self) -> object:
        """
        Walk the leaves only, left to right.
        """ 
        for k, v in self.items():
            if isinstance(v, dict):
                if v=={}:
                    yield v
                yield from v.leaves()
            else:
                yield v


    @property
    def printable(self) -> str:
        """
        Printing one of these things requires a bit of finesse.
        """
        return pprint.pformat(dict(self), compact=True, sort_dicts=True, indent=4, width=100)


    def traverse(self, with_indicator:bool=True) -> Union[Tuple[object, int], object]:
        """
        Emit all the nodes of a tree left-to-right and top-to-bottom.
        The bool is included so that you can know whether you have reached
        a leaf. 

        returns -- a tuple with the value of the node, and 1 => key, and 0 => leaf.

        Usages:
            for node, indicator in mytree.traverse(): ....
            for node in mytree.traverse(with_indicator=False): ....
                ....
        """

        for k, v in self.items():
            yield k, 1 if with_indicator else k
            if isinstance(v, dict):
                yield from v.traverse(with_indicator)
            else:
                yield v, 0 if with_indicator else v


    def as_tuples(self) -> tuple:
        """
        A generator to return all paths from root to leaves as 
        tuples of the nodes along the way.
        """
        tup = []
        for node, indicator in self.traverse():
            tup.append(node)
            if not indicator: 
                yield tuple(tup)
                tup = []        

    
    def iterate(self, dct):    
        for key, value in dct.items():
            print(f"dict-key {key} with kids {len(value)}")

            if isinstance(value, dict):
                self.iterate(value)


    def findIndicator(self, dct):
        for k, v in self.traverse():
            if v==0:
                return True


    def tree_as_table(self, nested_dict:SloppyTree=None, prepath=()):
        """
        Finds the path from the root to each leaf.
        """
        if nested_dict is None: nested_dict = self
        for k, v in nested_dict.items():
            path = prepath + (k,)
            #print("the path is here ", path)
            if isinstance(v, dict): # v is a dict
                if v=={}:
                    yield path
                else:
                    yield from self.tree_as_table(v, path)
            else:
                #### append the value of the leaf based on the key here
                path=path+(nested_dict.get(k), )
                yield path


    def dfs(self, start, end, visited, path, v):
        path.append(end)
        #print("???", start, end, v)
        return path

    def dfsPrinted(self,t):
        #visited = [False]*self.__len__()
        visited = []
        path = []
        for k, v in self.traverse():
            if k not in visited:
                path=[]
                visited.append(k)
                path = self.dfs(t, k, visited, path, v)     
                if v == 0:
                    path = visited 
                    visited = []
                    print("the path: ", path)


if __name__ == "__main__":
    t = SloppyTree()
    t.a.b.c
    t.a.b.c.d = 6
    t.a.b.d = 5
    t.a['c'].sixteen = "fred"

    for item in t.tree_as_table(t):
        print(f"path {item}")

 

    tt = SloppyTree()
    tt.kingdom
    tt.kingdom.animals
    tt.kingdom.animals.vertebrates
    tt.kingdom.animals.invertebrates
    tt.kingdom["plants"] = "gymnosperms", "angiosperms"
    tt.kingdom["fungi"]
    tt.kingdom.animals.vertebrates.mammals
    tt.kingdom.animals.vertebrates.mammals = "rodents", "mice", "hamsters"
    

    tt.kingdom.animals.vertebrates["reptile"] = "snakes", "chameleon"

    tt.kingdom.animals.invertebrates.mollusks = "oysters"
    tt.kingdom.animals.invertebrates.sponges = "brown", "yellow"
 

    print("number of paths", tt.__invert__())




    for item in tt.tree_as_table(tt):
        print(f"path {item}")
############## sloppytree (tree) utility code end ################
