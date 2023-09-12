# -*- coding: utf-8 -*-
import typing
from   typing import *

###
# Credits
###
__author__ = 'Alina Enikeeva'
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
mynetid = getpass.getuser()

###
# From hpclib
###
from   wrapper import trap

###
# imports that are a part of this project
###

###
# global objects
###
verbose = False
padding = lambda x: " "*x

@trap
def window_view_utils_main(myargs:argparse.Namespace) -> int:
    return os.EX_OK


@trap
def header():
    """
    The header of the window.
    """
    header = "Node".ljust(7)+"Cores"+padding(61)+"|  Memory\n"
    return header    

def subheader():
    """
    The subheader of the window.
    """
    subheader = padding(7) + "Allocated" + padding(52) +"Used" + padding(1) + "|  Alloc    Used   Total"
    return subheader

@trap
def help_msg() -> str:
    """
    Write help message here.
    """

    a = "This program displays the use of the Spydur.\n"
    b = "Next to the name of the node, you can see the map.\n It tells you how many cores (CPUs), out of 52, SLURM has allocated, \n based on the requests from users\n"
    c = "It happens that users request more cores than their program actually needs. \n The number that follows the map, indicates how many \n cores the node actually uses.\n"
    d = "Notice the 3 numbers that follow. Just like cores, these \n numbers indicate SLURM-allocated, actually-used and total \n memory in GB.\n"
    e = "If the node is colored in green, that means that its load \n is less than 75% in terms of both memory and CPU usage.\n"
    f = "If the node is colored yellow, that means that either node's\n memory or CPUs are more than 75% occupied.\n"  
    g = "The red color signifies anomaly - either the node is down or \n the number of cores used is more than 52.\n" 

    msg = "".join((a, b, c, d, e, f, g))

    return msg

@trap
def example_map():
    node1 = "spdr01 [XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX______]      37.38       48      50     384"
    node2 = "spdr02 [XXXXXXXXXXXXXXXXXXXXXXXX____________________________]      10.34       34      40     384"

    return list((node1, node2)) 
    

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="window_view_utils", 
        description="What window_view_utils does, window_view_utils does best.")

    parser.add_argument('-i', '--input', type=str, default="",
        help="Input file name.")
    parser.add_argument('-o', '--output', type=str, default="",
        help="Output file name")
    parser.add_argument('-v', '--verbose', action='store_true',
        help="Be chatty about what is taking place")


    myargs = parser.parse_args()
    verbose = myargs.verbose

    try:
        outfile = sys.stdout if not myargs.output else open(myargs.output, 'w')
        with contextlib.redirect_stdout(outfile):
            sys.exit(globals()[f"{os.path.basename(__file__)[:-3]}_main"](myargs))

    except Exception as e:
        print(f"Escaped or re-raised exception: {e}")

