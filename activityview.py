# -*- coding: utf-8 -*-
import typing
from   typing import *

min_py = (3, 8)

###
# Standard imports, starting with os and sys
###
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
import curses
import curses.panel
from   curses import wrapper
from   datetime import datetime
import getpass
import fcntl
import logging
import re
import shutil
import time
import math
mynetid = getpass.getuser()

import view_utils
from view_utils import *
from   wrapper import trap
from window_view_utils import *

###
# imports and objects that are a part of this project
###
verbose = False

###
# Credits
###
__author__ = 'Alina Enikeeva'
__copyright__ = 'Copyright 2022, University of Richmond'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'Alina Enikeeva, George Flanagin'
__email__ = 'hpc@richmond.edu'
__status__ = 'in progress'
__license__ = 'MIT'

DAT_FILE=os.path.join(os.getcwd(), 'info.dat')

suffix_keys = tuple("*~#!%$@^-")
suffix_values = (
    "not responding", "powered off", "powering on", "pending shutdown", "powering down",
    "reserved for maintenance", "pending reboot", "rebooting", "rescheduling"
    )
suffixes = dict(zip(suffix_keys, suffix_values))

state_keys = (  
    "alloc", "comp", "down", "drain", "drng", 
    "fail", "failg", "futr", "idle", "maint", 
    "mix", "pow_dn", "pow_up", "resv", "unk")
state_values = (
    "allocated", "completing", "down", "unavialable", "becoming unavailable", 
    "failed", "failing", "not yet configured", "idle", "maintenance", 
    "partially full", "powered down", "powering up", "reserved", "unknown state"
    )
states = dict(zip(state_keys, state_values))



@trap
def get_actual_cores_usage(node:str) -> int:
    """
    ssh to the node and get the number of cores that is actually used.
    """
    cmd = "ssh -o ConnectTimeout=1 {} 'cat /proc/loadavg'"
    result = view_utils.dorunrun(cmd.format(node), return_datatype = str)[:5]

    return 'None' if not result else result

@trap 
def get_actual_mem_usage(node:str) -> int:
    """
    ssh to the node and calculate how much memory is used.
    """
    pattern = re.compile(r'\d+')

    cmd = "ssh -o ConnectTimeout=1 {} 'head -2 cat /proc/meminfo'"
    result = view_utils.dorunrun(cmd.format(node), return_datatype = str) 
   

    if result == '':
        res = 'None'
    else:
        result = result.split("/n")
        memvals = re.findall(pattern, result[0])

        memtotal = int(memvals[0])
        memused = int(memvals[1])

        res = math.ceil((memtotal-memused)/1000000)

    return res

@trap
def get_list_of_nodes() -> dict:
    """
    Gets the current list of nodes as a dictionary whose
    keys are the node names, and whose values are the state 
    abbreviation and a boolean to indicate whether the node
    is reachable.
    """
    result = dorunrun('sinfo -o "%n %t"', return_datatype = str)
    info = result.split('\n')[1:]
    node_dict = {}
    for line in info:
        node, state = line.split()
        node_dict[node] = state

    return node_dict

@trap
def get_info() -> dict:
    global logger, myargs
    logger.info(piddly("get_info"))
    """
    Get the map with all the cores and memory information
    """
    global DAT_FILE, suffixes, states

    data = SeekINFO()
    core_map_and_mem = []
    actually_used_cores = {}   
    actually_used_mem = {}
    
    # multiprocessing to ssh to each node and get info on
    # actually used memory and cores
    fork_ssh(myargs.input) 
   
    # fork_ssh writes to info.dat
    # collect information into the dictionary
    with open(DAT_FILE) as infodat:
        #infodat.seek(0)
        
        for line in infodat.readlines():
            node = core = mem = ""
            try:
                node, core, mem = line.split()
                actually_used_cores[node] = core 
                actually_used_mem[node] = mem
            except Exception as e:
                logger.error(piddly(f"Failed to read {line=}"))

    for line in ( _ for _ in data.stdout.split('\n')[1:] if _ ):
        
        try: 
            node, free, total, status, true_cores, cores = line.split()
            cores = cores.split('/')
            allocated_mem = (int(total) - int(free))/1000 # GB
            alloc_cores = row(cores[0], true_cores)
            alloc_mem = str(math.ceil(allocated_mem))

            used_cores = actually_used_cores[node]
            used_mem = actually_used_mem[node]
            #print(node, used_cores, used_mem)
            total_mem_formatted = str(math.ceil(int(total)/1000))

            if used_cores == 'None':# or used_mem == 'None':
                suffix = ""
                text = ""
        
                if status[-1] in suffixes:
                    status, suffix = status[:-1], status[-1]
                    text = states.get(status, 'status unknown')
                    if suffix: text = f"{text} and {suffixes.get('suffix', 'N/A')}"
                core_map_and_mem.append(f"{node} is {text}.")
            else:
                core_map_and_mem.append(f"{node} {alloc_cores} {used_cores.rjust(10)} | {alloc_mem.rjust(6)}  {used_mem.rjust(6)}  {total_mem_formatted.rjust(6)} ")
        except Exception as e:
            logger.info(piddly(f"{e}"))

    return core_map_and_mem

@trap
def fork_ssh(list_of_nodes:dict) -> None:
    '''
    Multiprocesses to ssh to each node and retrieve this information 
    in parallel, significantly speeding up the process.
    '''
    global DAT_FILE, logger
    
    try:
        os.unlink(DAT_FILE)
    except FileNotFoundError as e:
        # This is OK; the file has already been deleted.
        pass

    except Exception as e:
        # This is something else, let's find out what happened.
        logger.error(piddly(f"Cannot continue. Unable to clear {DAT_FILE} because {e}."))
        sys.exit(os.EX_IOERR)

    pids = set()

    reachable_nodes = { node : state 
        for node, state in list_of_nodes.items() 
            if state[-1] not in suffixes and state[1:] not in 'd' }

    unreachable_nodes = { node : state 
        for node, state in list_of_nodes.items() 
            if node not in reachable_nodes }

    if len(unreachable_nodes): logger.info(piddly(f"{unreachable_nodes.keys()=}"))

    for node in reachable_nodes:            

        # Parent process records the child's PID.
        if (pid := os.fork()):
            pids.add(pid)
            continue

        with open(DAT_FILE, 'a+') as infodat:
            try:
                cores_used = -1
                mem_used = -1
                cores_used = get_actual_cores_usage(node)
                mem_used   = get_actual_mem_usage(node)    

                # each child process locks, writes to and unlocks the file
                fcntl.lockf(infodat, fcntl.LOCK_EX)
                infodat.write(f'{node} {cores_used} {mem_used}\n')
                infodat.close()
                
            except Exception as e:
                logger.error(piddly(f"query of {node} failed. {e}"))
                pass

            finally:
                logger.info(piddly(f"{node} {cores_used} {mem_used}"))
                os._exit(os.EX_OK)

    # make sure all the child processes finished before the function 
    # returns.
    while pids:
        # The zero in the argument means we wait for any child.
        # The resulting pid is the child that sent us a SIGCHLD.
        pid, exit_code, _ = os.wait3(0) 
        pids.remove(pid)

@trap
def how_busy(n:str) -> int:
    """
    Returns 0-n, corresponding to the activity on the node
    """
    data = SeekINFO()
    busy_cores = 0
    busy_mem = 0
   
    try: 
        n = n.split()[0]

        for line in ( _ for _ in data.stdout.split('\n')[1:] if _ ):
            node, free, total, status, true_cores, cores = line.split()
            if node == n:     
                cores = cores.split('/')
                busy_cores = int(cores[0])/int(true_cores)

                mem_used = int(total) - int(free)
                busy_mem = mem_used/int(total)
                
                break 
    except:
        pass

    return max(busy_cores, busy_mem) #, cores[1], true_cores

@trap
def map_cores(stdscr: object) -> None:

    """
    This method draws the map. It is an interactive window, 
    which can be refreshed. A window with help message is also 
    coded here.
    """

    global logger, myargs

    # initialize the color, use ID to refer to it later in the code
    # params: ID, font color, background color
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)

    #use the color, uses a variable assignment
    GREEN_AND_BLACK = curses.color_pair(1)
    YELLOW_AND_BLACK = curses.color_pair(2)
    WHITE_AND_BLACK = curses.color_pair(3)
    RED_AND_BLACK = curses.color_pair(4)    


    stdscr.clear()
    stdscr.nodelay(1) 

    # resize window if needed
    height,width = stdscr.getmaxyx()
    logger.info(piddly(f"Initialized a screen, {height}x{width}"))

    window2 = curses.newwin(0,0, 1,1)
    help_win = curses.newwin(0,0, 1,1)

    window2.bkgd(' ', WHITE_AND_BLACK)
    help_win.bkgd(' ', WHITE_AND_BLACK)

    left_panel = curses.panel.new_panel(window2)
    help_panel = curses.panel.new_panel(help_win)
    help_panel.hide()

    curses.panel.update_panels()
    curses.doupdate()

    running = True
    help_win_up = False
    x = 0
    
    while ( running ):
        #display the cores map for each node
        try:
            # window with help message
            if help_win_up:
                window2.clear()
                window2.refresh()
                left_panel.hide()
                help_panel.show()
                
                help_win.addstr(0, 0, header(), WHITE_AND_BLACK)
                help_win.addstr(1, 0, subheader(), WHITE_AND_BLACK)             
                help_win.addstr(3, 0, example_map()[0], YELLOW_AND_BLACK)
                help_win.addstr(4, 0, example_map()[1], GREEN_AND_BLACK)
                help_win.addstr(5, 0, help_msg(), WHITE_AND_BLACK)
    
                help_win.addstr(24, 0, "Press b to return to the main screen.")
                help_win.refresh()
                ch = help_win.getch()
                if ch == curses.KEY_RESIZE:    
                    height,width = stdscr.getmaxyx()
                    help_win.resize(height, width)
                    help_panel.replace(help_win)
                    help_panel.move(0,0)
                    help_panel.show()
                if ch == ord('b'): #or ch == ord('q'):
                    help_win_up = False
                    help_panel.hide()
                    help_win.clear()
                    continue    
                     
            # map the main window with CPU usage map and memory usage information.
            else:

                window2.addstr(0, 0, header(), WHITE_AND_BLACK)
                window2.addstr(1, 0, subheader(), WHITE_AND_BLACK)            

                info = get_info()
                
                for idx, node in enumerate(sorted(info)):
                    if 'is' in node: # red, if the node status is down or if numof cores used is > 52
                        window2.addstr(idx+2, 0, node, RED_AND_BLACK)
                    elif (float(node.split()[2])>52.00):
                        window2.addstr(idx+2, 0, node, RED_AND_BLACK)
                    elif how_busy(node) >= 0.75: #if node is more than 75% full
                        window2.addstr(idx+2, 0, node, YELLOW_AND_BLACK)
                    else:
                        window2.addstr(idx+2, 0, node, GREEN_AND_BLACK)
                window2.addstr(len(info)+2, 0, f'Last updated {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}', WHITE_AND_BLACK)
                window2.addstr(len(info)+3, 0, "Press q to quit, h for help OR any other key to refresh.", WHITE_AND_BLACK)
                window2.refresh()    
        except:
            pass 
        
        #work around window resize
        window2.timeout(myargs.refresh*1000)
        k = window2.getch()
        if k == -1:
            pass
        elif k == curses.KEY_RESIZE:    
            height,width = stdscr.getmaxyx()
            window2.resize(height, width)
            left_panel.replace(window2)
            left_panel.move(0,0)
        elif k == ord('q'): 
            running = False
            curses.endwin()

        # help message panel
        elif k == ord('h'):
            help_win_up = True
        
        curses.panel.update_panels()
        curses.doupdate()
        stdscr.refresh()
        window2.refresh()
    pass


@trap
def get_host_names(myargs:argparse.Namespace) -> dict:
    global logger

    hosts = tuple()
    if myargs.input:
        hosts = tuple(view_utils.read_whitespace_file(myargs.input))
        if not hosts or hosts == os.EX_NOINPUT:
            logger.info(piddly(f"Unable to use {myargs.input}"))
            sys.exit(os.EX_NOINPUT)
        return dict.fromkeys(hosts, "")

    else:
        return  get_list_of_nodes()
        

@trap
def piddly(s:str) -> str:
    """
    Prepend the PID to a string (for logging).
    """
    return f": {os.getppid()} <- {os.getpid()} : {s}"

@trap
def activityview_main() -> int:
    #wrapper(draw_menu)
    global logger, myargs
    logger.info(piddly("Entered activityview_main"))

    myargs.input=get_host_names(myargs)
    wrapper(map_cores)
    return os.EX_OK


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="activityview", 
        description="What activityview does, activityview does best.")

    parser.add_argument('-r', '--refresh', type=int, default=60, 
        help="Refresh interval defaults to 60 seconds. Set to 0 to only run once.")
    parser.add_argument('-i', '--input', type=str, default="",
        help="If present, --input is interpreted to be a whitespace delimited file of host names.")
    parser.add_argument('-o', '--output', type=str, default="",
        help="Output file name")
    parser.add_argument('-v', '--verbose', type=int, default=logging.DEBUG, 
        help=f"Sets the loglevel. Values between {logging.NOTSET} and {logging.CRITICAL}.")


    myargs = parser.parse_args()

    verbose = myargs.verbose if logging.NOTSET <= myargs.verbose <= logging.CRITICAL else logging.DEBUG
    logger = view_utils.URLogger(level=myargs.verbose)
    
    ###
    # Make an effort to ensure SLURM is on this system.
    ###
    slurm_installed = bool(shutil.which('sinfo'))

    if not slurm_installed:
        print("This does not appear to be a SLURM system.")
        sys.exit(os.EX_SOFTWARE)


    try:
        outfile = sys.stdout if not myargs.output else open(myargs.output, 'w')
        with contextlib.redirect_stdout(outfile):
            sys.exit(globals()[f"{os.path.basename(__file__)[:-3]}_main"]())

    except Exception as e:
        print(f"Escaped or re-raised exception: {e}")

